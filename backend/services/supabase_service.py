"""
Mentora - Supabase Database Service
Supabase database service.
"""

import time
import logging
from typing import Optional

from .supabase_client import supabase

logger = logging.getLogger(__name__)


class SupabaseService:

    # Sessions

    def create_session(self, session_id: str, doc: dict):
        data = {
            "id": session_id,
            "user_id": doc.get("user_id"),
            "started_at": doc.get("started_at", time.time()),
            "ended_at": doc.get("ended_at"),
            "status": doc.get("status", "active"),
            "frame_count": doc.get("frame_count", 0),
            "avg_fatigue": doc.get("avg_fatigue", 0),
            "peak_fatigue": doc.get("peak_fatigue", 0),
        }

        result = supabase.table("sessions").upsert(data).execute()
        return result.data

    def get_session(self, session_id: str) -> Optional[dict]:
        result = (
            supabase
            .table("sessions")
            .select("*")
            .eq("id", session_id)
            .maybe_single()
            .execute()
        )

        return result.data

    def update_session_metrics(self, session_id: str, new_score: float):
        session = self.get_session(session_id)

        if not session:
            return

        frame_count = int(session.get("frame_count") or 0) + 1
        previous_avg = float(session.get("avg_fatigue") or 0)
        previous_peak = float(session.get("peak_fatigue") or 0)

        new_avg = (
            (previous_avg * (frame_count - 1) + new_score)
            / frame_count
        )

        update = {
            "frame_count": frame_count,
            "avg_fatigue": round(new_avg, 1),
            "peak_fatigue": max(previous_peak, new_score),
        }

        supabase.table("sessions").update(update).eq(
            "id", session_id
        ).execute()

    def finalise_session(self, session_id: str) -> dict:
        entries = self.get_fatigue_entries(session_id)

        scores = [
            float(entry.get("fatigue_score") or 0)
            for entry in entries
        ]

        update = {
            "ended_at": time.time(),
            "status": "completed",
            "avg_fatigue": round(
                sum(scores) / len(scores), 1
            ) if scores else 0,
            "peak_fatigue": max(scores) if scores else 0,
        }

        supabase.table("sessions").update(update).eq(
            "id", session_id
        ).execute()

        return update

    # Fatigue entries

    def add_fatigue_entry(self, session_id: str, doc: dict):
        data = {
            "session_id": session_id,
            "timestamp": doc.get("timestamp", time.time()),
            "fatigue_score": doc.get("fatigue_score", 0),
            "state": doc.get("state"),
            "ear": doc.get("ear"),
            "mar": doc.get("mar"),
        }

        return (
            supabase
            .table("fatigue_entries")
            .insert(data)
            .execute()
        )

    def get_fatigue_entries(self, session_id: str) -> list:
        result = (
            supabase
            .table("fatigue_entries")
            .select("*")
            .eq("session_id", session_id)
            .order("timestamp")
            .execute()
        )

        return result.data or []

    # Session list & delete

    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> list:

        result = (
            supabase
            .table("sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("started_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return result.data or []

    def delete_session(self, session_id: str):
        supabase.table("sessions").delete().eq(
            "id", session_id
        ).execute()

    # User preferences

    def get_user_preferences(self, user_id: str) -> dict:
        result = (
            supabase
            .table("profiles")
            .select("preferences")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )

        if not result.data:
            return {}

        return result.data.get("preferences") or {}

    def set_user_preferences(self, user_id: str, prefs: dict):
        result = (
            supabase
            .table("profiles")
            .upsert(
                {
                    "id": user_id,
                    "preferences": prefs,
                    "updated_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ",
                        time.gmtime()
                    ),
                },
                on_conflict="id",
            )
            .execute()
        )

        return result.data

    # Weekly analytics

    def get_weekly_analytics(self, user_id: str) -> dict:
        cutoff = time.time() - 7 * 86400

        result = (
            supabase
            .table("sessions")
            .select("*")
            .eq("user_id", user_id)
            .gte("started_at", cutoff)
            .execute()
        )

        sessions = result.data or []

        daily = {}

        for session in sessions:
            started_at = session.get("started_at")

            if not started_at:
                continue

            day = time.strftime(
                "%Y-%m-%d",
                time.localtime(started_at)
            )

            daily.setdefault(
                day,
                {
                    "date": day,
                    "sessions": 0,
                    "_fatigue_sum": 0,
                    "avg_fatigue": 0,
                    "total_time_min": 0,
                },
            )

            daily[day]["sessions"] += 1

            daily[day]["_fatigue_sum"] += float(
                session.get("avg_fatigue") or 0
            )

            daily[day]["avg_fatigue"] = round(
                daily[day]["_fatigue_sum"]
                / daily[day]["sessions"],
                1,
            )

            ended_at = session.get("ended_at") or time.time()

            duration = (
                (ended_at - started_at) / 60
            )

            daily[day]["total_time_min"] = round(
                daily[day]["total_time_min"] + duration,
                1,
            )

        for day in daily.values():
            day.pop("_fatigue_sum", None)

        return {
            "days": sorted(
                daily.values(),
                key=lambda item: item["date"]
            )
        }



