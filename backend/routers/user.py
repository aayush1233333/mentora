"""
Mentora – User Preferences Router
GET /user/preferences        → fetch stored prefs
PUT /user/preferences        → upsert prefs
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from services.supabase_service import SupabaseService
from services.auth_service import get_current_user

router   = APIRouter()
supabase_service = SupabaseService()


class Preferences(BaseModel):
    displayName:        Optional[str]   = None
    captureRate:        Optional[int]   = 2
    thresholdPreset:    Optional[str]   = "Normal"
    notifyBrowser:      Optional[bool]  = True
    notifyOnStressed:   Optional[bool]  = True
    notifyOnFatigued:   Optional[bool]  = True
    breakReminderMins:  Optional[int]   = 45
    enableVoice:        Optional[bool]  = False
    enableTTS:          Optional[bool]  = False
    pomodoroMinutes:    Optional[int]   = 25
    showEARMAR:         Optional[bool]  = True
    notificationToken:           Optional[str]   = None


@router.get("/user/preferences")
async def get_preferences(user=Depends(get_current_user)):
    prefs = supabase_service.get_user_preferences(user["uid"])
    return prefs or {}


@router.put("/user/preferences")
async def update_preferences(body: Preferences, user=Depends(get_current_user)):
    data = body.model_dump(exclude_none=True)
    supabase_service.set_user_preferences(user["uid"], data)
    return {"message": "Preferences saved", "preferences": data}



