"""
Mentora – Wellness Tips Router
GET /wellness/tip?state=Stressed&score=52   → contextual micro-tip
GET /wellness/tips?state=Fatigued&n=3       → batch of tips
"""

from fastapi import APIRouter, Depends, Query
from services.auth_service import get_current_user
from services.wellness_tips import WellnessTipsService

router = APIRouter()
_tips  = WellnessTipsService()


@router.get("/wellness/tip")
async def get_tip(
    state: str  = Query(default="Normal"),
    score: float = Query(default=0),
    user=Depends(get_current_user),
):
    return _tips.get_tip(state=state, score=score)  # type: ignore


@router.get("/wellness/tips")
async def get_tips_batch(
    state: str = Query(default="Normal"),
    n:     int = Query(default=3, ge=1, le=10),
    user=Depends(get_current_user),
):
    return {"tips": _tips.get_batch(state=state, n=n)}  # type: ignore


