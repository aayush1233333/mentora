"""
Mentora – Firebase Service
Wraps Firestore CRUD operations.
Set GOOGLE_APPLICATION_CREDENTIALS env var to your service-account JSON path.
"""

import json
import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_STUB_MODE = False  # flipped to True if Firebase unavailable


def _load_credentials(credentials):
    service_account_json = (
        os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    )
    if service_account_json and service_account_json.strip():
        return credentials.Certificate(json.loads(service_account_json))

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and cred_path.strip():
        cred_path = cred_path.strip()
        if cred_path.lstrip().startswith("{"):
            return credentials.Certificate(json.loads(cred_path))
        if os.path.exists(cred_path):
            return credentials.Certificate(cred_path)

    return credentials.ApplicationDefault()

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        cred = _load_credentials(credentials)
        firebase_admin.initialize_app(cred)

    _db_name = os.getenv("FIRESTORE_DATABASE_ID", "(default)")
    _db = firestore.client(database=_db_name)
    logger.info(f"Firestore connected ✓ (database={_db_name})")
except Exception as e:
    logger.warning(f"Firebase unavailable ({e}) – using in-memory stub.")
    _db         = None
    _STUB_MODE  = True


# ── In-memory stub (unit tests / no-Firebase environments) ───────────────────
_stub: dict = {"sessions": {}, "fatigue": {}, "users": {}}


class FirebaseService:

    # ── Sessions ──────────────────────────────────────────────────────────────

    def create_session(self, session_id: str, doc: dict):
        if _STUB_MODE:
            _stub["sessions"][session_id] = doc; return
        _db.collection("sessions").document(session_id).set(doc)

    def get_session(self, session_id: str) -> Optional[dict]:
        if _STUB_MODE:
            return _stub["sessions"].get(session_id)
        snap = _db.collection("sessions").document(session_id).get()
        return snap.to_dict() if snap.exists else None

    def update_session_metrics(self, session_id: str, new_score: float):
        """
        Lightweight per-frame update. Only increments frame_count atomically.

        peak_fatigue and avg_fatigue are NOT computed here: Firestore has no
        atomic MAX() operation (firebase_admin.firestore.MAX does not exist —
        the old hasattr() guard always failed and silently fell back to
        overwriting peak_fatigue with the latest score, which is wrong).

        Instead, every frame's score is already persisted via
        add_fatigue_entry() into the fatigue_data subcollection, so both
        avg_fatigue and peak_fatigue are derived correctly in one pass over
        that subcollection at finalise_session() time — see below.
        """
        if _STUB_MODE:
            s = _stub["sessions"].get(session_id, {})
            s["frame_count"]  = s.get("frame_count", 0) + 1
            count             = s["frame_count"]
            prev_avg          = s.get("avg_fatigue", 0)
            s["avg_fatigue"]  = round((prev_avg * (count - 1) + new_score) / count, 1)
            s["peak_fatigue"] = max(s.get("peak_fatigue", 0), new_score)
            return
        ref = _db.collection("sessions").document(session_id)
        from firebase_admin import firestore as _fs
        ref.update({"frame_count": _fs.Increment(1)})

    def finalise_session(self, session_id: str) -> dict:
        entries = self.get_fatigue_entries(session_id)
        scores  = [e.get("fatigue_score", 0) for e in entries]
        update  = {
            "ended_at":     time.time(),
            "status":       "completed",
            "avg_fatigue":  round(sum(scores) / len(scores), 1) if scores else 0,
            "peak_fatigue": max(scores) if scores else 0,
        }
        if _STUB_MODE:
            _stub["sessions"].get(session_id, {}).update(update)
            return update
        _db.collection("sessions").document(session_id).update(update)
        return update

    # ── Fatigue entries ───────────────────────────────────────────────────────

    def add_fatigue_entry(self, session_id: str, doc: dict):
        if _STUB_MODE:
            _stub["fatigue"].setdefault(session_id, []).append(doc); return
        _db.collection("sessions").document(session_id)\
           .collection("fatigue_data").add(doc)

    def get_fatigue_entries(self, session_id: str) -> list:
        if _STUB_MODE:
            return _stub["fatigue"].get(session_id, [])
        snaps = _db.collection("sessions").document(session_id)\
                   .collection("fatigue_data")\
                   .order_by("timestamp").stream()
        return [s.to_dict() for s in snaps]

    # ── Session list & delete ─────────────────────────────────────────────────

    def get_user_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> list:
        if _STUB_MODE:
            sessions = [s for s in _stub["sessions"].values() if s.get("user_id") == user_id]
            sessions.sort(key=lambda s: s.get("started_at", 0), reverse=True)
            return sessions[offset:offset + limit]
        snaps = (_db.collection("sessions")
                   .where("user_id", "==", user_id)
                   .order_by("started_at", direction="DESCENDING")
                   .limit(limit)
                   .offset(offset)
                   .stream())
        return [s.to_dict() for s in snaps]

    def delete_session(self, session_id: str):
        if _STUB_MODE:
            _stub["sessions"].pop(session_id, None)
            _stub["fatigue"].pop(session_id, None)
            return
        # Delete sub-collection entries first
        for doc in (_db.collection("sessions").document(session_id)
                       .collection("fatigue_data").stream()):
            doc.reference.delete()
        _db.collection("sessions").document(session_id).delete()

    # ── User preferences ──────────────────────────────────────────────────────

    def get_user_preferences(self, user_id: str) -> dict:
        if _STUB_MODE:
            return _stub["users"].get(user_id, {}).get("preferences", {})
        snap = _db.collection("users").document(user_id).get()
        return snap.to_dict().get("preferences", {}) if snap.exists else {}

    def set_user_preferences(self, user_id: str, prefs: dict):
        if _STUB_MODE:
            _stub["users"].setdefault(user_id, {})["preferences"] = prefs
            return
        _db.collection("users").document(user_id).set(
            {"preferences": prefs}, merge=True)

    # ── Weekly analytics ──────────────────────────────────────────────────────

    def get_weekly_analytics(self, user_id: str) -> dict:
        cutoff = time.time() - 7 * 86400
        if _STUB_MODE:
            sessions = [s for s in _stub["sessions"].values()
                        if s.get("user_id") == user_id and
                           s.get("started_at", 0) >= cutoff]
        else:
            snaps    = _db.collection("sessions")\
                          .where("user_id", "==", user_id)\
                          .where("started_at", ">=", cutoff)\
                          .stream()
            sessions = [s.to_dict() for s in snaps]

        daily: dict = {}
        for s in sessions:
            day = time.strftime("%Y-%m-%d", time.localtime(s["started_at"]))
            daily.setdefault(day, {
                "date": day,
                "sessions": 0,
                "_fatigue_sum": 0,   # internal accumulator, stripped before return
                "avg_fatigue": 0,
                "total_time_min": 0,
            })
            daily[day]["sessions"]     += 1
            daily[day]["_fatigue_sum"] += s.get("avg_fatigue", 0)
            daily[day]["avg_fatigue"]   = round(
                daily[day]["_fatigue_sum"] / daily[day]["sessions"], 1)
            duration = ((s.get("ended_at") or time.time()) - s["started_at"]) / 60
            daily[day]["total_time_min"] = round(daily[day]["total_time_min"] + duration, 1)

        # Strip the internal accumulator before returning to callers.
        for d in daily.values():
            d.pop("_fatigue_sum", None)

        return {"days": sorted(daily.values(), key=lambda x: x["date"])}
