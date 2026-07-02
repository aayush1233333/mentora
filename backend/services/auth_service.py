"""
Mentora – Auth Service
Verifies Firebase ID tokens sent in the Authorization header (REST)
or as a ?token= query parameter (WebSocket).
"""

import os
import logging
from fastapi import Header, HTTPException, status, WebSocket

logger = logging.getLogger(__name__)
_STUB_USER = {"uid": "dev-user-001", "email": "dev@mentora.ai"}


async def _verify_token(token: str) -> dict | None:
    """
    Core token verification logic shared by REST and WebSocket paths.
    Returns a user dict on success, or None if the token is invalid.
    Falls back to the stub user in development when Firebase is unavailable.
    """
    env = os.getenv("ENV", "development")
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth

        if not firebase_admin._apps:
            if env == "development":
                logger.warning("Firebase Admin not initialized – returning stub user.")
                return _STUB_USER
            return None

        decoded = firebase_auth.verify_id_token(token)
        return {"uid": decoded["uid"], "email": decoded.get("email", "")}
    except ImportError:
        if env == "development":
            logger.warning("firebase_admin not available – returning stub user.")
            return _STUB_USER
        return None
    except Exception as e:
        if env == "development":
            logger.warning(f"Token verification failed in dev – returning stub user. Error: {e}")
            return _STUB_USER
        return None


async def get_current_user(authorization: str = Header(default="")) -> dict:
    """
    Expects: Authorization: Bearer <firebase-id-token>
    Falls back to a dev stub when Firebase is not configured.
    """
    env = os.getenv("ENV", "development")

    if not authorization.startswith("Bearer "):
        if env == "development":
            return _STUB_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    token = authorization.removeprefix("Bearer ").strip()
    user = await _verify_token(token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


async def verify_ws_token(websocket: WebSocket, token: str = "") -> dict | None:
    """
    WebSocket authentication via ?token=<firebase-id-token> query param.

    Usage in a WebSocket endpoint:
        async def ws_endpoint(websocket: WebSocket, token: str = Query(default="")):
            user = await verify_ws_token(websocket, token)
            if user is None:
                return  # connection already closed with code 4001

    Returns the user dict on success, or None after closing the socket with 4001.
    """
    env = os.getenv("ENV", "development")

    if not token:
        if env == "development":
            logger.warning("WS: no token provided – returning stub user in development.")
            return _STUB_USER
        await websocket.close(code=4001, reason="Missing authentication token")
        return None

    user = await _verify_token(token)
    if user is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return None

    return user
