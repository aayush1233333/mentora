"""
Mentora – Chatbot Router
POST /chatbot ? mental wellness AI powered by Gemini 2.5 Flash
"""

import os
import logging
from fastapi import APIRouter, Depends
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
    message: str
    fatigue_score: float | None = None
    state: str | None = None
    history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []


@router.post("/chatbot", response_model=ChatResponse)
async def chatbot(body: ChatRequest, user=Depends(get_current_user)):
    context = ""

    if body.fatigue_score is not None:
        context = (
            f"[User's current fatigue score: {body.fatigue_score}/100, "
            f"state: {body.state}] "
        )

    user_msg = context + body.message

    history_lines = []

    for h in body.history[-10:]:
        role = h.get("role", "user")
        content = h.get("content", "")

        if content:
            history_lines.append(f"{role}: {content}")

    history_text = "\n".join(history_lines)

    prompt = SYSTEM_PROMPT

    if history_text:
        prompt += f"\n\nConversation history:\n{history_text}"

    prompt += f"\n\nCurrent user message:\n{user_msg}"

    # -- Gemini 2.5 Flash ---------------------------------------------
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            reply = response.text.strip()

            if reply:
                return ChatResponse(reply=reply)

        except Exception as e:
            logger.warning(
                f"Gemini error: {e} – falling back to rule-based response."
            )

    # -- Rule-based fallback -------------------------------------------
    reply = _rule_based_reply(
        body.message,
        body.fatigue_score,
        body.state,
    )

    return ChatResponse(reply=reply)


def _rule_based_reply(
    msg: str,
    score: float | None,
    state: str | None,
) -> str:

    msg_lower = msg.lower()

    if score is not None and score >= 65:
        return (
            "Your fatigue score is quite high. Consider taking a 10-minute break, "
            "stepping away from screens, and doing some light stretching. "
            "Staying hydrated and taking a short walk can significantly help recovery."
        )

    if "stress" in msg_lower or state == "Stressed":
        return (
            "Try the 4-7-8 breathing technique: inhale for 4 seconds, hold for 7, "
            "exhale for 8. This activates your parasympathetic nervous system and "
            "can help reduce stress."
        )

    if "tired" in msg_lower or "fatigue" in msg_lower:
        return (
            "Cognitive fatigue often builds gradually. The Pomodoro technique "
            "(25 min focus + 5 min break) can help maintain mental stamina. "
            "Also ensure you're drinking enough water."
        )

    if "help" in msg_lower or "advice" in msg_lower:
        return (
            "I'm here to help! I can suggest breathing exercises, break reminders, "
            "or mindfulness techniques based on your real-time fatigue score. "
            "What specifically are you struggling with today?"
        )

    return (
        "I'm tracking your cognitive state in real time. Keep an eye on your "
        "fatigue score dashboard and take breaks when needed. Is there something "
        "specific on your mind?"
    )
