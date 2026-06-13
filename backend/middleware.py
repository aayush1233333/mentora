"""
Mentora – Middleware
  • RateLimitMiddleware  – token-bucket per IP for /process-frame
  • RequestLogMiddleware – structured request/response logging
  • SecurityHeadersMiddleware – OWASP security headers
"""

import time
import uuid
import logging
from collections import defaultdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Token-bucket rate limiter
# ─────────────────────────────────────────────────────────────────────────────

class _Bucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity    = capacity
        self.tokens      = float(capacity)
        self.refill_rate = refill_rate   # tokens / second
        self.last_refill = time.monotonic()

    def consume(self, n: int = 1) -> bool:
        now    = time.monotonic()
        delta  = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + delta * self.refill_rate)
        self.last_refill = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Applies per-IP rate limits to expensive endpoints.
    Default: /process-frame → 10 req/s burst, 5 req/s sustained.
    """

    LIMITS = {
        "/api/v1/process-frame": (10, 5.0),   # (burst_capacity, refill_rate)
        "/api/v1/chatbot":       (5,  1.0),
    }

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, dict[str, _Bucket]] = defaultdict(dict)

    def _get_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        return forwarded.split(",")[0].strip() if forwarded else request.client.host or "unknown"

    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight requests to pass through immediately
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path in self.LIMITS:
            ip       = self._get_ip(request)
            cap, rate = self.LIMITS[path]

            if path not in self._buckets[ip]:
                self._buckets[ip][path] = _Bucket(cap, rate)

            if not self._buckets[ip][path].consume():
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Slow down frame submission."},
                    headers={"Retry-After": "1"},
                )

        return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────────
# Request logging
# ─────────────────────────────────────────────────────────────────────────────

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight requests to pass through immediately
        if request.method == "OPTIONS":
            return await call_next(request)

        req_id = str(uuid.uuid4())[:8]
        start  = time.perf_counter()

        # Skip logging health checks to reduce noise
        if request.url.path == "/health":
            return await call_next(request)

        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000

        logger.info(
            "%s  %s %s  %d  %.1fms",
            req_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        response.headers["X-Request-ID"] = req_id
        return response


# ─────────────────────────────────────────────────────────────────────────────
# Security headers
# ─────────────────────────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    HEADERS = {
        "X-Content-Type-Options":  "nosniff",
        "X-Frame-Options":         "DENY",
        "X-XSS-Protection":        "1; mode=block",
        "Referrer-Policy":         "strict-origin-when-cross-origin",
        "Permissions-Policy":      "camera=(self), microphone=(self), geolocation=()",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }

    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight requests to pass through without adding security headers
        # that could interfere with the CORS response
        if request.method == "OPTIONS":
            return await call_next(request)

        response = await call_next(request)
        for key, value in self.HEADERS.items():
            response.headers[key] = value
        return response
