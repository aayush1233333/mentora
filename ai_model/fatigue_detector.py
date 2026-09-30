"""
Mentora - Fatigue Detector Core
Uses MediaPipe Tasks (FaceLandmarker) + EAR/MAR feature extraction.

NOTE: This was migrated from the legacy `mp.solutions.face_mesh` API to the
current `mp.tasks.vision.FaceLandmarker` API. Google ended support for
MediaPipe Legacy Solutions on March 1, 2023, and as of mid-2025/2026 the
`mp.solutions` submodule is no longer reliably bundled in PyPI wheels for
several platforms (observed: Linux x86_64, the platform GitHub Actions
runners use). The legacy API call `mp.solutions.face_mesh.FaceMesh(...)`
raises `AttributeError: module 'mediapipe' has no attribute 'solutions'`
on those builds. See: https://ai.google.dev/edge/mediapipe/solutions/guide

Landmark indices (LEFT_EYE_IDX, RIGHT_EYE_IDX, MOUTH_IDX) are UNCHANGED —
the new FaceLandmarker uses the same 468/478-point face mesh topology as
the legacy FaceMesh solution, just with a different access path to reach
the per-landmark x/y/z coordinates.
"""

from collections import deque
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks_python
from mediapipe.tasks.python import vision as mp_tasks_vision
import numpy as np
from scipy.spatial import distance as dist

logger = logging.getLogger(__name__)

try:
    from head_pose import HeadPoseEstimator

    _HEAD_POSE_AVAILABLE = True
except ImportError:
    _HEAD_POSE_AVAILABLE = False

# MediaPipe indices for eyes / mouth. Unchanged from the legacy FaceMesh
# topology — the FaceLandmarker task uses the same 478-point face model.
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [61, 291, 39, 269, 0, 17]

# Thresholds.
EAR_THRESHOLD = 0.22
MAR_THRESHOLD = 0.65
BLINK_CONSEC = 3
YAWN_OPEN_THRESHOLD = 0.60
YAWN_CLOSE_THRESHOLD = 0.45
YAWN_MIN_DURATION = 1.5
FATIGUE_WINDOW = 90

# Path to the FaceLandmarker .task model bundle. Expected to be downloaded
# into ai_model/weights/face_landmarker.task during the Docker build (see
# backend/Dockerfile) or CI setup (see .github/workflows/ci.yml) — it is
# NOT committed to the repo (binary, ~3.7MB, gitignored).
#
# Override with the MEDIAPIPE_FACE_LANDMARKER_MODEL_PATH env var if you
# store it somewhere else (e.g. a mounted volume in a different deployment).
_DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "weights" / "face_landmarker.task"
MODEL_PATH = Path(os.getenv("MEDIAPIPE_FACE_LANDMARKER_MODEL_PATH", str(_DEFAULT_MODEL_PATH)))


class FatigueDetector:
    """
    Real-time fatigue and stress detection from facial landmarks.
    Returns a FatigueResult dict compatible with the FastAPI layer.
    """

    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"FaceLandmarker model not found at {MODEL_PATH}. "
                "Download it with:\n"
                "  curl -L -o "
                f"{MODEL_PATH} "
                "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
                "face_landmarker/float16/latest/face_landmarker.task\n"
                "or set MEDIAPIPE_FACE_LANDMARKER_MODEL_PATH to its location."
            )

        base_options = mp_tasks_python.BaseOptions(model_asset_path=str(MODEL_PATH))
        options = mp_tasks_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_tasks_vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self.face_landmarker = mp_tasks_vision.FaceLandmarker.create_from_options(options)

        self.ear_buffer: deque = deque(maxlen=FATIGUE_WINDOW)
        self.mar_buffer: deque = deque(maxlen=FATIGUE_WINDOW)
        self.fatigue_score_buffer: deque = deque(maxlen=FATIGUE_WINDOW)

        self._pose_estimator = HeadPoseEstimator() if _HEAD_POSE_AVAILABLE else None

        self.blink_counter = 0
        self.blink_total = 0
        self.yawn_counter = 0
        self.yawn_total = 0
        self._yawn_started_at: Optional[float] = None
        self._yawn_active = False
        self.frame_count = 0
        self.session_start = time.time()

        self._last_minute_blinks = deque(maxlen=300)
        self._timestamps: deque = deque(maxlen=300)

    def close(self):
        """Releases the underlying FaceLandmarker task graph. Call this when
        a session ends to free native resources (mirrors the DetectorPool
        cleanup pattern in backend/services/detector_service.py)."""
        if hasattr(self, "face_landmarker") and self.face_landmarker is not None:
            self.face_landmarker.close()
            self.face_landmarker = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def _eye_aspect_ratio(landmarks, eye_indices, w, h) -> float:
        pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]
        a = dist.euclidean(pts[1], pts[5])
        b = dist.euclidean(pts[2], pts[4])
        c = dist.euclidean(pts[0], pts[3])
        return (a + b) / (2.0 * c + 1e-6)

    @staticmethod
    def _mouth_aspect_ratio(landmarks, mouth_indices, w, h) -> float:
        pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in mouth_indices]
        a = dist.euclidean(pts[2], pts[4])
        b = dist.euclidean(pts[3], pts[5])
        c = dist.euclidean(pts[0], pts[1])
        return (a + b) / (2.0 * c + 1e-6)

    def _compute_fatigue_score(self, ear: float, mar: float) -> float:
        if len(self.ear_buffer) < 10:
            return 0.0

        avg_ear = np.mean(self.ear_buffer)
        avg_mar = np.mean(self.mar_buffer)

        ear_baseline = max(np.percentile(list(self.ear_buffer), 90), 0.28)
        ear_drop_pct = max(0, (ear_baseline - avg_ear) / ear_baseline)

        elapsed = max((time.time() - self.session_start) / 60, 0.01)
        bpm = self.blink_total / elapsed
        blink_score = min(abs(bpm - 17) / 17, 1.0)

        yawn_score = min(self.yawn_total / max(elapsed, 1) * 2, 1.0)
        mar_score = min(max(avg_mar - 0.4, 0) / 0.4, 1.0)

        raw = (ear_drop_pct * 0.45 + blink_score * 0.25 + yawn_score * 0.20 + mar_score * 0.10)
        return round(min(raw * 100, 100), 1)

    def _classify_state(self, score: float, mar: float, ear: float) -> str:
        if score >= 65 or ear < EAR_THRESHOLD * 0.85:
            return "Fatigued"
        if score >= 35 or mar > MAR_THRESHOLD:
            return "Stressed"
        return "Normal"

    def _update_blink_state(self, ear: float) -> None:
        if ear < EAR_THRESHOLD:
            self.blink_counter += 1
            return

        if self.blink_counter >= BLINK_CONSEC:
            self.blink_total += 1
        self.blink_counter = 0

    def _update_yawn_state(self, mar: float, now: Optional[float] = None) -> None:
        now = now or time.time()

        if self._yawn_active:
            if mar <= YAWN_CLOSE_THRESHOLD:
                self._yawn_active = False
                self._yawn_started_at = None
                self.yawn_counter = 0
            return

        if mar >= YAWN_OPEN_THRESHOLD:
            if self._yawn_started_at is None:
                self._yawn_started_at = now
                self.yawn_counter = 1
                return

            self.yawn_counter += 1
            if now - self._yawn_started_at >= YAWN_MIN_DURATION:
                self.yawn_total += 1
                self._yawn_active = True
            return

        self._yawn_started_at = None
        self.yawn_counter = 0

    def process_frame(self, frame_bgr: np.ndarray) -> Dict:
        """
        Args:
            frame_bgr: OpenCV BGR frame (numpy array)
        Returns:
            dict with keys: fatigue_score, state, ear, mar,
                            blink_count, yawn_count, landmarks_detected
        """
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # FaceLandmarker (mp.tasks) requires the input wrapped in an
        # mp.Image, unlike the legacy FaceMesh.process() which accepted a
        # raw numpy array directly.
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.face_landmarker.detect(mp_image)

        if not result.face_landmarks:
            return self._empty_result()

        # New API: result.face_landmarks[0] is a list of NormalizedLandmark
        # objects with the same .x / .y / .z attributes as the legacy API's
        # result.multi_face_landmarks[0].landmark — so everything downstream
        # of `lm` (EAR/MAR math, head pose) is unchanged.
        lm = result.face_landmarks[0]

        ear_l = self._eye_aspect_ratio(lm, LEFT_EYE_IDX, w, h)
        ear_r = self._eye_aspect_ratio(lm, RIGHT_EYE_IDX, w, h)
        ear = (ear_l + ear_r) / 2.0
        mar = self._mouth_aspect_ratio(lm, MOUTH_IDX, w, h)

        self.ear_buffer.append(ear)
        self.mar_buffer.append(mar)
        self.frame_count += 1

        now = time.time()
        self._update_blink_state(ear)
        self._update_yawn_state(mar, now)

        pitch, yaw, roll = (0.0, 0.0, 0.0)
        if self._pose_estimator:
            pitch, yaw, roll = self._pose_estimator.estimate(lm)

        score = self._compute_fatigue_score(ear, mar)
        state = self._classify_state(score, mar, ear)
        self.fatigue_score_buffer.append(score)

        return {
            "fatigue_score": score,
            "state": state,
            "ear": round(ear, 4),
            "mar": round(mar, 4),
            "blink_count": self.blink_total,
            "yawn_count": self.yawn_total,
            "landmarks_detected": True,
            "frame_number": self.frame_count,
            "head_pitch": round(pitch, 2),
            "head_yaw": round(yaw, 2),
        }

    def _empty_result(self) -> Dict:
        return {
            "fatigue_score": 0,
            "state": "Unknown",
            "ear": 0,
            "mar": 0,
            "blink_count": self.blink_total,
            "yawn_count": self.yawn_total,
            "landmarks_detected": False,
            "frame_number": self.frame_count,
        }

    def reset(self):
        self.ear_buffer.clear()
        self.mar_buffer.clear()
        self.fatigue_score_buffer.clear()
        self.blink_counter = self.blink_total = 0
        self.yawn_counter = self.yawn_total = 0
        self._yawn_started_at = None
        self._yawn_active = False
        self.frame_count = 0
        self.session_start = time.time()

    def get_session_summary(self) -> Dict:
        elapsed = time.time() - self.session_start
        avg_ear = float(np.mean(list(self.ear_buffer))) if self.ear_buffer else 0
        avg_fatigue_score = (
            float(np.mean(list(self.fatigue_score_buffer)))
            if self.fatigue_score_buffer else 0
        )
        return {
            "duration_seconds":  round(elapsed, 1),
            "total_blinks":      self.blink_total,
            "total_yawns":       self.yawn_total,
            "avg_ear":           round(avg_ear, 4),
            "avg_fatigue_score": round(avg_fatigue_score, 1),
            "frames_processed":  self.frame_count,
        }
