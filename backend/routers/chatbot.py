"""
Mentora – Chatbot Router
POST /chatbot  → mental wellness AI powered by Claude/OpenAI
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.auth_service import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Mentora, a compassionate AI wellness coach integrated into a cognitive fatigue tracking system.
Your role:
- Provide evidence-based mental wellness guidance
- Suggest evidence-backed techniques: breathing, mindfulness, movement breaks, hydration
- Interpret fatigue scores: 0-30 Normal, 31-65 Moderate stress/tiredness, 66-100 Severe fatigue
- Keep responses concise (3-5 sentences), warm, and actionable
- Never diagnose medical conditions; always suggest professional help for serious concerns
- Personalise based on the user's current fatigue state if provided in context

Tone: supportive, non-judgmental, science-informed, brief."""


class ChatRequest(BaseModel):
    message:       str
    fatigue_score: float | None = None
    state:         str | None   = None
    history:       list[dict]   = []   # [{role: user|assistant, content: str}]


class ChatResponse(BaseModel):
    reply:    str
    sources:  list[str] = []


@router.post("/chatbot", response_model=ChatResponse)
async def chatbot(body: ChatRequest, user=Depends(get_current_user)):
    context = ""
    if body.fatigue_score is not None:
        context = f"[User's current fatigue score: {body.fatigue_score}/100, state: {body.state}] "

    user_msg = context + body.message

    messages = []
    for h in body.history[-10:]:    # last 10 turns
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    # ── Try OpenAI ────────────────────────────────────────────────────────────
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            resp   = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                max_tokens=300,
                temperature=0.7,
            )
            return ChatResponse(reply=resp.choices[0].message.content.strip())
        except Exception as e:
            logger.warning(f"OpenAI error: {e} – falling back to rule-based.")

    # ── Rule-based fallback ───────────────────────────────────────────────────
    reply = _rule_based_reply(body.message, body.fatigue_score, body.state)
    return ChatResponse(reply=reply)


def _rule_based_reply(msg: str, score: float | None, state: str | None) -> str:
    msg_lower = msg.lower()
    if score and score >= 65:
        return ("Your fatigue score is quite high. Consider taking a 10-minute break, "
                "stepping away from screens, and doing some light stretching. "
                "Staying hydrated and taking a short walk can significantly help recovery.")
    if "stress" in msg_lower or (state == "Stressed"):
        return ("Try the 4-7-8 breathing technique: inhale for 4 seconds, hold for 7, "
                "exhale for 8. This activates your parasympathetic nervous system and "
                "reduces stress hormones within minutes.")
    if "tired" in msg_lower or "fatigue" in msg_lower:
        return ("Cognitive fatigue often builds gradually. The Pomodoro technique "
                "(25 min focus + 5 min break) is excellent for maintaining mental stamina. "
                "Also ensure you're drinking enough water — dehydration worsens fatigue.")
    if "help" in msg_lower or "advice" in msg_lower:
        return ("I'm here to help! I can suggest breathing exercises, break reminders, "
                "or mindfulness techniques based on your real-time fatigue score. "
                "What specifically are you struggling with today?")
    return ("I'm tracking your cognitive state in real time. Keep an eye on your fatigue "
            "score dashboard — I'll send you a notification when a break is recommended. "
            "Is there something specific on your mind?")


