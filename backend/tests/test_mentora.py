"""
Mentora – Backend Test Suite
Run: pytest tests/ -v
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# AI Model tests
# ─────────────────────────────────────────────────────────────────────────────

# FatigueDetector now uses the MediaPipe Tasks FaceLandmarker API which
# requires a downloaded .task model file at ai_model/weights/face_landmarker.task.
# In CI this file is fetched by the "Download FaceLandmarker model" step.
# Locally, run: curl -L -o ai_model/weights/face_landmarker.task \
#   https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
_MODEL_PATH = Path(__file__).resolve().parents[3] / "ai_model" / "weights" / "face_landmarker.task"
_MODEL_AVAILABLE = _MODEL_PATH.exists()

# Also verify the MediaPipe Tasks C++ runtime can actually load.
# It needs EGL/GLES shared libraries even on headless systems.
# We catch BaseException (not just Exception) since ctypes OSError
# can sometimes propagate outside normal exception hierarchy on some platforms.
if _MODEL_AVAILABLE:
    try:
        import mediapipe as _mp
        from mediapipe.tasks import python as _mpt
        from mediapipe.tasks.python import vision as _mptv
        _base_opts = _mpt.BaseOptions(model_asset_path=str(_MODEL_PATH))
        _fl_opts  = _mptv.FaceLandmarkerOptions(
            base_options=_base_opts,
            running_mode=_mptv.RunningMode.IMAGE,
        )
        _probe = _mptv.FaceLandmarker.create_from_options(_fl_opts)
        _probe.close()
        del _base_opts, _fl_opts, _probe
        _DETECTOR_AVAILABLE = True
    except BaseException:
        _DETECTOR_AVAILABLE = False
else:
    _DETECTOR_AVAILABLE = False

@pytest.mark.skipif(not _DETECTOR_AVAILABLE, reason=(
    "FaceLandmarker not available: model file missing or MediaPipe Tasks "
    "C++ runtime failed to load (libGLESv2.so.2 missing — "
    "install: sudo apt-get install libgles2)"
))
class TestFatigueDetector:
    """Tests for the rule-based fatigue detector (no real webcam needed)."""

    def setup_method(self):
        from ai_model.fatigue_detector import FatigueDetector
        self.detector = FatigueDetector()

    def test_empty_result_no_face(self):
        """Black frame → no landmarks → empty result."""
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        result = self.detector.process_frame(black)
        assert result["landmarks_detected"] is False
        assert result["fatigue_score"] == 0
        assert result["state"] == "Unknown"

    def test_result_keys_present(self):
        """Result dict must contain all expected keys."""
        black = np.zeros((480, 640, 3), dtype=np.uint8)
        result = self.detector.process_frame(black)
        expected_keys = {
            "fatigue_score", "state", "ear", "mar",
            "blink_count", "yawn_count", "landmarks_detected", "frame_number"
        }
        assert expected_keys.issubset(result.keys())

    def test_reset_clears_state(self):
        self.detector.blink_total = 5
        self.detector.yawn_total  = 2
        self.detector.reset()
        assert self.detector.blink_total == 0
        assert self.detector.yawn_total  == 0
        assert len(self.detector.ear_buffer) == 0

    def test_session_summary_keys(self):
        summary = self.detector.get_session_summary()
        for key in ("duration_seconds", "total_blinks", "total_yawns", "frames_processed"):
            assert key in summary

    def test_ear_below_threshold_increments_blink_counter(self):
        """Simulate below-EAR frames to trigger blink counting."""
        from ai_model.fatigue_detector import EAR_THRESHOLD, BLINK_CONSEC
        self.detector.ear_buffer.extend([0.30] * 20)  # prime baseline

        for _ in range(BLINK_CONSEC):
            self.detector._update_blink_state(EAR_THRESHOLD - 0.01)
        self.detector._update_blink_state(EAR_THRESHOLD + 0.02)
        assert self.detector.blink_total == 1

    def test_sustained_open_mouth_counts_single_yawn(self):
        from ai_model.fatigue_detector import (
            YAWN_CLOSE_THRESHOLD,
            YAWN_MIN_DURATION,
            YAWN_OPEN_THRESHOLD,
        )

        start = 100.0
        self.detector._update_yawn_state(YAWN_OPEN_THRESHOLD + 0.05, start)
        self.detector._update_yawn_state(YAWN_OPEN_THRESHOLD + 0.05, start + (YAWN_MIN_DURATION / 2))
        assert self.detector.yawn_total == 0

        self.detector._update_yawn_state(YAWN_OPEN_THRESHOLD + 0.05, start + YAWN_MIN_DURATION + 0.1)
        assert self.detector.yawn_total == 1

        self.detector._update_yawn_state(YAWN_OPEN_THRESHOLD + 0.08, start + YAWN_MIN_DURATION + 0.6)
        assert self.detector.yawn_total == 1

        self.detector._update_yawn_state(YAWN_CLOSE_THRESHOLD - 0.05, start + YAWN_MIN_DURATION + 0.8)
        self.detector._update_yawn_state(YAWN_OPEN_THRESHOLD + 0.05, start + 4.0)
        self.detector._update_yawn_state(YAWN_OPEN_THRESHOLD + 0.05, start + 4.0 + YAWN_MIN_DURATION + 0.1)
        assert self.detector.yawn_total == 2


class TestFatigueModel:
    def test_rule_based_normal(self):
        from ai_model.cnn_lstm_model import FatigueModel
        model = FatigueModel()
        fv = np.array([0.30, 0.40, 0.45, 0.10, 0.5, 0.5])
        state, conf = model.predict(fv)
        assert state in ("Normal", "Stressed", "Fatigued")
        assert 0.0 <= conf <= 1.0

    def test_rule_based_fatigued(self):
        from ai_model.cnn_lstm_model import FatigueModel
        model = FatigueModel()
        fv = np.array([0.18, 0.40, 0.20, 0.10, 0.5, 0.5])  # very low EAR
        state, conf = model.predict(fv)
        assert state == "Fatigued"

    def test_rule_based_stressed_yawn(self):
        from ai_model.cnn_lstm_model import FatigueModel
        model = FatigueModel()
        fv = np.array([0.27, 0.70, 0.45, 0.10, 0.5, 0.5])  # high MAR
        state, _ = model.predict(fv)
        assert state == "Stressed"

    def test_reset_clears_sequence(self):
        from ai_model.cnn_lstm_model import FatigueModel
        model = FatigueModel()
        model.seq_buf = [[0]*6]*10
        model.reset_sequence()
        assert len(model.seq_buf) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Firebase service (stub mode)
# ─────────────────────────────────────────────────────────────────────────────

class TestFirebaseServiceStub:
    def setup_method(self):
        # Force stub mode
        import backend.services.firebase_service as fs_mod
        fs_mod._STUB_MODE = True
        fs_mod._stub = {"sessions": {}, "fatigue": {}, "users": {}}
        from backend.services.firebase_service import FirebaseService
        self.svc = FirebaseService()

    def test_create_and_get_session(self):
        doc = {"session_id": "s1", "user_id": "u1", "started_at": 0.0, "status": "active",
               "avg_fatigue": 0, "peak_fatigue": 0, "frame_count": 0}
        self.svc.create_session("s1", doc)
        got = self.svc.get_session("s1")
        assert got is not None
        assert got["session_id"] == "s1"

    def test_get_missing_session(self):
        result = self.svc.get_session("nonexistent")
        assert result is None

    def test_add_and_get_fatigue_entries(self):
        self.svc.create_session("s2", {"session_id": "s2", "user_id": "u1",
                                       "started_at": 0, "status": "active",
                                       "avg_fatigue": 0, "peak_fatigue": 0, "frame_count": 0})
        for i in range(3):
            self.svc.add_fatigue_entry("s2", {"timestamp": float(i), "fatigue_score": 10*i, "state": "Normal"})
        entries = self.svc.get_fatigue_entries("s2")
        assert len(entries) == 3

    def test_finalise_session(self):
        self.svc.create_session("s3", {"session_id": "s3", "user_id": "u1",
                                       "started_at": 0, "status": "active",
                                       "avg_fatigue": 0, "peak_fatigue": 0, "frame_count": 0})
        self.svc.add_fatigue_entry("s3", {"fatigue_score": 40, "state": "Stressed"})
        self.svc.add_fatigue_entry("s3", {"fatigue_score": 60, "state": "Fatigued"})
        summary = self.svc.finalise_session("s3")
        assert summary["status"] == "completed"
        assert summary["avg_fatigue"] == 50.0


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI endpoint tests (TestClient)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Returns a FastAPI TestClient with auth stubbed out."""
    import importlib, os
    os.environ["ENV"] = "development"  # enable stub auth

    # Stub Firebase before importing app
    with patch.dict("sys.modules", {
        "firebase_admin":          MagicMock(),
        "firebase_admin.credentials": MagicMock(),
        "firebase_admin.firestore":   MagicMock(),
        "firebase_admin.auth":        MagicMock(),
    }):
        from fastapi.testclient import TestClient
        import backend.main as app_module
        return TestClient(app_module.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_start_session_returns_id(client):
    resp = client.post("/api/v1/start-session",
                       json={},
                       headers={"Authorization": "Bearer stub"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 10


def test_process_frame_invalid_b64(client):
    resp = client.post("/api/v1/process-frame",
                       json={"session_id": "test", "frame_b64": "!!!invalid!!!"},
                       headers={"Authorization": "Bearer stub"})
    assert resp.status_code == 422


def test_chatbot_returns_reply(client):
    resp = client.post("/api/v1/chatbot",
                       json={"message": "I feel tired", "fatigue_score": 70, "state": "Fatigued"},
                       headers={"Authorization": "Bearer stub"})
    assert resp.status_code == 200
    assert "reply" in resp.json()
    assert len(resp.json()["reply"]) > 0


def test_weekly_report_empty(client):
    resp = client.get("/api/v1/reports/weekly",
                      headers={"Authorization": "Bearer stub"})
    assert resp.status_code == 200
    assert "days" in resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# Report service
# ─────────────────────────────────────────────────────────────────────────────

class TestReportService:
    def test_build_pdf_returns_bytes(self):
        from backend.services.report_service import build_pdf_report
        report = {
            "session": {"session_id": "abc", "started_at": 0, "ended_at": 100},
            "analytics": {
                "avg_fatigue_score": 42, "peak_fatigue_score": 75,
                "min_fatigue_score": 10, "duration_minutes": 1.7,
                "total_frames": 50,
                "state_distribution": {"Normal": 30, "Stressed": 15, "Fatigued": 5}
            },
            "timeline": []
        }
        pdf = build_pdf_report(report)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
