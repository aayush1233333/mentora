"""
Mentora – FastAPI Application Entry Point
"""
import os
import logging
import re
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from middleware import RateLimitMiddleware, RequestLogMiddleware, SecurityHeadersMiddleware

load_dotenv(Path(__file__).with_name(".env"))

from routers import (
    session, frames, reports, chatbot,
    websocket_router, sessions_list, user, wellness, health
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
class _SensitiveQueryFilter(logging.Filter):
    _pattern = re.compile(
        r"([?&](?:access_token|refresh_token|token)=)[^&\s\"']+",
        re.IGNORECASE,
    )

    def _redact(self, value):
        if isinstance(value, str):
            return self._pattern.sub(r"\1[REDACTED]", value)
        if isinstance(value, tuple):
            return tuple(self._redact(item) for item in value)
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, dict):
            return {
                key: self._redact(item)
                for key, item in value.items()
            }
        return value

    def filter(self, record):
        record.msg = self._redact(record.msg)
        record.args = self._redact(record.args)
        return True


for _access_logger_name in ("uvicorn.access", "uvicorn.error", "gunicorn.access"):
    logging.getLogger(_access_logger_name).addFilter(
        _SensitiveQueryFilter()
    )

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    logger.info(f"🌐 CORS origins: {cors_origins}")
    logger.info("🧠  Mentora backend starting up …")
    yield
    logger.info("🔴  Mentora backend shutting down.")


app = FastAPI(
    title="Mentora API",
    version="1.0.0",
    description="Cognitive Fatigue & Well-Being Tracker – REST + WebSocket API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware stack (registered last = outermost = runs first) ───────────────
#
#   Request flow:  SecurityHeaders → RequestLog → RateLimit → CORS → GZip → route
#   Response flow: route → GZip → CORS → RateLimit → RequestLog → SecurityHeaders
#
# CORS must be innermost so that rate-limit 429s still carry correct CORS headers.
# SecurityHeaders must be outermost so every response (including 429s) gets them.

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    max_age=600,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(session.router,          prefix="/api/v1", tags=["Session"])
app.include_router(sessions_list.router,    prefix="/api/v1", tags=["Sessions"])
app.include_router(frames.router,           prefix="/api/v1", tags=["Frames"])
app.include_router(reports.router,          prefix="/api/v1", tags=["Reports"])
app.include_router(chatbot.router,          prefix="/api/v1", tags=["Chatbot"])
app.include_router(user.router,             prefix="/api/v1", tags=["User"])
app.include_router(wellness.router,         prefix="/api/v1", tags=["Wellness"])
app.include_router(websocket_router.router,                   tags=["WebSocket"])

