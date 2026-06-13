"""
Mentora – Frames Router
POST /process-frame  → decodes base64 JPEG, runs fatigue detector, stores result
"""

import base64
import time
import numpy as np
import cv2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.firebase_service import FirebaseService
from services.auth_service import get_current_user
from services.detector_service import DetectorPool

router   = APIRouter()
firebase = FirebaseService()
pool     = DetectorPool()


class ProcessFrameRequest(BaseModel):
    session_id: str
    frame_b64:  str          # base64-encoded JPEG (no data-URI prefix)
    timestamp:  float | None = None


class ProcessFrameResponse(BaseModel):
    fatigue_score:      float
    state:              str
    ear:                float
    mar:                float
    blink_count:        int
    yawn_count:         int
    landmarks_detected: bool


@router.post("/process-frame", response_model=ProcessFrameResponse)
async def process_frame(
    body: ProcessFrameRequest,
    user=Depends(get_current_user),
):
    # ── Decode frame ────────────────────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(body.frame_b64)
        nparr     = np.frombuffer(img_bytes, np.uint8)
        frame     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid frame data")

    if frame is None:
        raise HTTPException(status_code=422, detail="Could not decode image")

    # ── Run detector ────────────────────────────────────────────────────────
    detector = pool.get(body.session_id)
    result   = detector.process_frame(frame)

    ts = body.timestamp or time.time()

    # ── Persist to Firestore (non-blocking via background task ideally) ──────
    fatigue_doc = {
        "session_id":    body.session_id,
        "user_id":       user["uid"],
        "timestamp":     ts,
        "fatigue_score": result["fatigue_score"],
        "state":         result["state"],
        "ear":           result["ear"],
        "mar":           result["mar"],
        "blink_count":   result["blink_count"],
        "yawn_count":    result["yawn_count"],
    }
    firebase.add_fatigue_entry(body.session_id, fatigue_doc)
    firebase.update_session_metrics(body.session_id, result["fatigue_score"])

    return ProcessFrameResponse(**result)
