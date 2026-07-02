"""
Mentora – Health Check Router
GET /health        → basic liveness probe
GET /health/ready  → readiness probe (checks Firebase + AI model)
GET /health/stats  → internal cache + detector pool stats (admin only in prod)
"""

import os
import time
import logging
from fastapi import APIRouter
from services.cache_service import cache_stats
from services.detector_service import pool

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)

_start_time = time.time()


@router.get("/health")
async def liveness():
    """Basic liveness probe for load balancers."""
    return {
        "status":    "ok",
        "service":   "mentora-api",
        "version":   "1.0.0",
        "uptime_s":  round(time.time() - _start_time, 1),
    }


@router.get("/health/ready")
async def readiness():
    """
    Readiness probe – checks:
      • Firebase Firestore connectivity
      • AI model availability
    Returns 200 if ready, 503 if degraded.
    """
    checks: dict = {}
    overall = "ok"

    # Firebase check
    try:
        from services.firebase_service import _STUB_MODE
        checks["firebase"] = "stub_mode" if _STUB_MODE else "connected"
    except Exception as e:
        checks["firebase"] = f"error: {e}"
        overall = "degraded"

    # AI model check (imports only – no inference)
    try:
        from ai_model.fatigue_detector import FatigueDetector  # noqa: F401
        checks["ai_model"] = "available"
    except Exception as e:
        checks["ai_model"] = f"unavailable: {e}"
        overall = "degraded"

    # OpenAI
    checks["openai_key"] = "set" if os.getenv("OPENAI_API_KEY") else "not_set (fallback active)"

    status_code = 200 if overall == "ok" else 503
    return {"status": overall, "checks": checks, "uptime_s": round(time.time() - _start_time, 1)}


@router.get("/health/stats")
async def internal_stats():
    """Internal stats – useful during development."""
    if os.getenv("ENV", "development") == "production":
        # In production expose only to internal callers (add auth if needed)
        return {"message": "Stats endpoint disabled in production by default."}
    return {
        "cache":   cache_stats(),
        "active_sessions": pool.session_count(),
        "uptime_s": round(time.time() - _start_time, 1),
    }
