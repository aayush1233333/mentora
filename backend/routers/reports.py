"""
Mentora – Reports Router
GET /report?session_id=...  → full analytics + optional PDF export
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import time

from services.supabase_service import SupabaseService
from services.auth_service import get_current_user
from services.report_service import build_pdf_report

router   = APIRouter()
supabase_service = SupabaseService()


@router.get("/report")
async def get_report(
    session_id: str = Query(...),
    format:     str = Query("json", regex="^(json|pdf)$"),
    user=Depends(get_current_user),
):
    session = supabase_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["user_id"] != user["uid"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    entries = supabase_service.get_fatigue_entries(session_id)

    report = _build_report(session, entries)

    if format == "pdf":
        pdf_bytes = build_pdf_report(report)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="mentora_report_{session_id[:8]}.pdf"'},
        )

    return report


@router.get("/reports/weekly")
async def weekly_analytics(user=Depends(get_current_user)):
    """Return aggregated daily stats for the past 7 days (cached 5 min)."""
    from services.cache_service import cache_get, cache_set
    cache_key = f"weekly:{user['uid']}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    data = supabase_service.get_weekly_analytics(user["uid"])
    cache_set(cache_key, data, ttl=300)
    return data


def _build_report(session: dict, entries: list) -> dict:
    if not entries:
        return {"session": session, "analytics": {}, "timeline": []}

    scores    = [e["fatigue_score"] for e in entries if "fatigue_score" in e]
    states    = [e["state"] for e in entries if "state" in e]
    duration  = (session.get("ended_at") or time.time()) - session["started_at"]

    state_counts = {"Normal": 0, "Stressed": 0, "Fatigued": 0, "Unknown": 0}
    for s in states:
        state_counts[s] = state_counts.get(s, 0) + 1

    analytics = {
        "avg_fatigue_score":   round(sum(scores) / len(scores), 1) if scores else 0,
        "peak_fatigue_score":  round(max(scores), 1) if scores else 0,
        "min_fatigue_score":   round(min(scores), 1) if scores else 0,
        "state_distribution":  state_counts,
        "duration_minutes":    round(duration / 60, 1),
        "total_frames":        len(entries),
    }

    # Downsample timeline to ≤200 points for chart performance
    step     = max(1, len(entries) // 200)
    timeline = [
        {"t": e["timestamp"], "score": e["fatigue_score"], "state": e["state"]}
        for e in entries[::step]
    ]

    return {"session": session, "analytics": analytics, "timeline": timeline}


