"""
Mentora - Detector Pool
Manages one FatigueDetector instance per active session.

This module owns the single, process-wide DetectorPool instance (`pool`).
All routers must import `pool` from here rather than instantiating their
own DetectorPool() — multiple instances each get their own empty dict,
which silently breaks session lookup, cleanup, and health stats.
"""

import sys
import threading
from pathlib import Path


_HERE = Path(__file__).resolve()
_AI_MODEL_CANDIDATES = (
    _HERE.parents[2] / "ai_model",  # repo root / ai_model
    _HERE.parents[1] / "ai_model",  # Docker /app/ai_model
)

for _ai_model_dir in _AI_MODEL_CANDIDATES:
    if _ai_model_dir.exists():
        sys.path.insert(0, str(_ai_model_dir))
        sys.path.insert(0, str(_ai_model_dir.parent))
        break

from fatigue_detector import FatigueDetector


class DetectorPool:
    """Thread-safe pool of per-session FatigueDetector objects."""

    def __init__(self):
        self._pool: dict[str, FatigueDetector] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> FatigueDetector:
        with self._lock:
            if session_id not in self._pool:
                self._pool[session_id] = FatigueDetector()
            return self._pool[session_id]

    def remove(self, session_id: str):
        with self._lock:
            self._pool.pop(session_id, None)

    def summary(self, session_id: str) -> dict:
        with self._lock:
            d = self._pool.get(session_id)
        return d.get_session_summary() if d else {}

    def session_count(self) -> int:
        with self._lock:
            return len(self._pool)


# ── Process-wide singleton ────────────────────────────────────────────────────
# Import this, don't instantiate your own DetectorPool().
pool = DetectorPool()
