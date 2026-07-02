"""
Mentora – WebSocket Router
ws://host/ws/{session_id}?token=<firebase-id-token>  → real-time fatigue stream
"""

import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from services.connection_manager import ConnectionManager
from services.firebase_service import FirebaseService
from services.auth_service import verify_ws_token

router   = APIRouter()
manager  = ConnectionManager()
firebase = FirebaseService()
logger   = logging.getLogger(__name__)

# How long to wait for a client message before sending a server-side keepalive ping.
# The loop continues after the ping — the connection is NOT dropped on timeout.
_RECEIVE_TIMEOUT = 30  # seconds


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(default=""),
):
    # ── Authenticate before joining the session ───────────────────────────────
    # verify_ws_token accepts the socket first (required by the WS protocol),
    # then immediately closes it with code 4001 if the token is missing/invalid.
    user = await verify_ws_token(websocket, token)
    if user is None:
        return  # socket already closed inside verify_ws_token

    await manager.connect(websocket, session_id)
    logger.info(f"WS connected: {session_id} (uid={user['uid']})")
    try:
        while True:
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(), timeout=_RECEIVE_TIMEOUT
                )
            except asyncio.TimeoutError:
                # No message from client in 30 s — send a keepalive ping and
                # go back to waiting.  Do NOT exit the loop here.
                await websocket.send_json({"type": "ping"})
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"WS invalid JSON from [{session_id}]: {raw[:80]}")
                continue

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe_session":
                pass  # already subscribed via route param

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info(f"WS disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WS error [{session_id}]: {e}")
        manager.disconnect(websocket, session_id)
