"""
Mentora – FastAPI Application Entry Point
Run: uvicorn main:app --reload --port 8000
Production: gunicorn -c gunicorn.conf.py main:app
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response

load_dotenv(Path(__file__).with_name(".env"))

from routers import (
    session, frames, reports, chatbot,
    websocket_router, sessions_list, user, wellness, health
)
from middleware import RateLimitMiddleware, RequestLogMiddleware, SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
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

# ── Middleware (registered outer → inner) ─────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global OPTIONS handler for CORS preflight ─────────────────────────────────
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        }
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)                                          # /health*
app.include_router(session.router,       prefix="/api/v1", tags=["Session"])
app.include_router(sessions_list.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(frames.router,        prefix="/api/v1", tags=["Frames"])
app.include_router(reports.router,       prefix="/api/v1", tags=["Reports"])
app.include_router(chatbot.router,       prefix="/api/v1", tags=["Chatbot"])
app.include_router(user.router,          prefix="/api/v1", tags=["User"])
app.include_router(wellness.router,      prefix="/api/v1", tags=["Wellness"])
app.include_router(websocket_router.router,                tags=["WebSocket"])
