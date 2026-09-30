"""
Mentora – Backend Test Suite
Run: pytest tests/ -v
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# AI Model tests
# ─────────────────────────────────────────────────────────────────────────────

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
# Database service
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



