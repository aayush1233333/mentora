"""
Mentora – Session Router
POST /start-session  → creates a new session document in Firestore
POST /end-session    → finalises the session
"""

import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from services.firebase_service import FirebaseService
from services.auth_service import get_current_user
from services.detector_service import pool

router = APIRouter()
firebase = FirebaseService()


class StartSessionRequest(BaseModel):
    device_info: dict | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    started_at: float
    message: str


class EndSessionRequest(BaseModel):
    session_id: str


@router.post("/start-session", response_model=StartSessionResponse)
async def start_session(
    body: StartSessionRequest,
    user=Depends(get_current_user),
):
    session_id = str(uuid.uuid4())
    now = time.time()

    session_doc = {
        "session_id":   session_id,
        "user_id":      user["uid"],
        "started_at":   now,
        "ended_at":     None,
        "device_info":  body.device_info or {},
        "status":       "active",
        "frame_count":  0,
        "avg_fatigue":  0,
        "peak_fatigue": 0,
    }
    firebase.create_session(session_id, session_doc)
    return StartSessionResponse(
        session_id=session_id,
        started_at=now,
        message="Session started",
    )


@router.post("/end-session")
async def end_session(
    body: EndSessionRequest,
    user=Depends(get_current_user),
):
    session = firebase.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["user_id"] != user["uid"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    summary = firebase.finalise_session(body.session_id)

    # Release the FatigueDetector instance for this session (frees the
    # MediaPipe FaceMesh model from memory). Without this, every completed
    # session leaks its detector indefinitely.
    pool.remove(body.session_id)

    return {"message": "Session ended", "summary": summary}
