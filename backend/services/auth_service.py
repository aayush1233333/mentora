"""
Mentora - Auth Service
Verifies Supabase JWTs sent in the Authorization header (REST)
or as a ?token= query parameter (WebSocket).
"""

import os
import logging
from fastapi import Header, HTTPException, status, WebSocket
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_JWKS_URL = (
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    if SUPABASE_URL
    else ""
)

_STUB_USER = {
    "uid": "00000000-0000-0000-0000-000000000000",
    "email": "dev@mentora.ai",
}

_jwks_client = (
    PyJWKClient(SUPABASE_JWKS_URL)
    if SUPABASE_JWKS_URL
    else None
)


async def _verify_token(token: str) -> dict | None:
    """
    Verify a Supabase access token using the project's public JWKS key.
    """

    env = os.getenv("ENV", "development")

    if not _jwks_client:
        if env == "development":
            logger.warning(
                "Supabase JWKS is not configured - returning stub user."
            )
            return _STUB_USER
        return None

    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)

        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={
                "verify_aud": False,
            },
        )

        user_id = decoded.get("sub")

        if not user_id:
            return None

        return {
            "uid": user_id,
            "email": decoded.get("email", ""),
        }

    except Exception as e:
        logger.exception("Supabase token verification failed: %s", e)

        if env == "development":
            return _STUB_USER

        return None


async def get_current_user(
    authorization: str = Header(default="")
) -> dict:
    """
    Expects:
        Authorization: Bearer <supabase-access-token>
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


async def verify_ws_token(
    websocket: WebSocket,
    token: str = ""
) -> dict | None:
    """
    WebSocket authentication via:
        ?token=<supabase-access-token>
    """

    env = os.getenv("ENV", "development")

    if not token:
        if env == "development":
            logger.warning(
                "WS: no token provided - returning stub user in development."
            )
            return _STUB_USER

        await websocket.close(
            code=4001,
            reason="Missing authentication token",
        )
        return None

    user = await _verify_token(token)

    if user is None:
        await websocket.close(
            code=4001,
            reason="Invalid or expired token",
        )
        return None

    return user


