"""
Mentora – Wellness Tips Service
Returns contextual, evidence-based micro-tips based on fatigue state and time of day.
"""

import random
import time
from typing import Literal

State = Literal["Normal", "Stressed", "Fatigued", "Unknown"]

TIPS: dict[str, list[dict]] = {
    "Normal": [
        {"title": "Maintain your rhythm",    "body": "You're doing great. Keep taking micro-breaks every 25 min to sustain this level.",       "icon": "✓"},
        {"title": "Hydration check",         "body": "Drink a glass of water now. Mild dehydration reduces concentration by up to 20%.",        "icon": "💧"},
        {"title": "Posture reset",           "body": "Roll your shoulders back, lift your chin slightly, and take 3 slow breaths.",             "icon": "🧍"},
        {"title": "Screen distance",         "body": "Your eyes should be 50–70 cm from the screen. Adjust now to prevent strain.",            "icon": "👁"},
        {"title": "Blink intentionally",     "body": "Staring at screens reduces blink rate by 60%. Blink deliberately 10 times right now.",    "icon": "😌"},
    ],
    "Stressed": [
        {"title": "4-7-8 breath now",        "body": "Inhale 4s → hold 7s → exhale 8s. Repeat 3 times to activate your vagus nerve.",         "icon": "🌬"},
        {"title": "Progressive muscle relax","body": "Tense your shoulders for 5s then release. Work down from neck to hands.",                 "icon": "💪"},
        {"title": "Cold water splash",       "body": "Splashing cold water on your face triggers the diving reflex, slowing your heart rate.",   "icon": "🚰"},
        {"title": "5-4-3-2-1 grounding",    "body": "Name 5 things you see, 4 you hear, 3 you can touch, 2 you smell, 1 you taste.",           "icon": "🌿"},
        {"title": "Jaw release",             "body": "Stress stores in the jaw. Open wide, hold 3s, release. Repeat 5 times.",                  "icon": "😮"},
    ],
    "Fatigued": [
        {"title": "Take a real break",       "body": "15–20 min break recommended. Step outside or lie down — not just scroll your phone.",      "icon": "☕"},
        {"title": "NASA nap",                "body": "A 10-min nap improves alertness by 30%. Set an alarm and close your eyes now.",           "icon": "😴"},
        {"title": "Light movement",          "body": "5 min of walking increases brain blood flow by 11%. Just stand up and move.",             "icon": "🚶"},
        {"title": "Eye recovery",            "body": "Look at something 20 feet away for 20 seconds. Your ciliary muscles need the rest.",       "icon": "👀"},
        {"title": "Natural light",           "body": "Go outside or near a window. Natural light resets circadian rhythm and boosts alertness.", "icon": "☀️"},
    ],
    "Unknown": [
        {"title": "Start monitoring",        "body": "Enable the webcam to get real-time fatigue tracking and personalised wellness tips.",     "icon": "📷"},
    ],
}

# Time-of-day contextual tips appended to Normal state
MORNING_TIPS = [
    {"title": "Morning intention",  "body": "Write 3 things you want to accomplish today. Clarity reduces cognitive load by 23%.", "icon": "📝"},
]
AFTERNOON_TIPS = [
    {"title": "Afternoon dip",      "body": "The 2–3 PM slump is biological. A 15-min walk or short rest is more effective than caffeine.", "icon": "⏰"},
]
EVENING_TIPS = [
    {"title": "Wind-down routine",  "body": "Dim your screen brightness now. Blue light suppresses melatonin — start winding down.", "icon": "🌙"},
]


class WellnessTipsService:
    def __init__(self):
        self._last_tip: dict | None = None

    def get_tip(self, state: State = "Normal", score: float = 0) -> dict:
        """Returns a contextual tip for the given state, avoiding repetition."""
        pool = list(TIPS.get(state, TIPS["Normal"]))

        # Add time-of-day tips for Normal state
        if state == "Normal":
            hour = time.localtime().tm_hour
            if 5 <= hour < 11:
                pool.extend(MORNING_TIPS)
            elif 13 <= hour < 16:
                pool.extend(AFTERNOON_TIPS)
            elif hour >= 20:
                pool.extend(EVENING_TIPS)

        # Avoid repeating the last tip
        if self._last_tip and len(pool) > 1:
            pool = [t for t in pool if t["title"] != self._last_tip.get("title")]

        tip = random.choice(pool)
        self._last_tip = tip

        # Add urgency for high scores
        if score >= 70:
            tip = dict(tip)
            tip["urgent"] = True
            tip["body"] += " This is important — your score is critically high."

        return tip

    def get_batch(self, state: State = "Normal", n: int = 3) -> list[dict]:
        """Returns n unique tips for the given state."""
        pool = list(TIPS.get(state, TIPS["Normal"]))
        random.shuffle(pool)
        return pool[:n]

