# gunicorn.conf.py  –  Production Gunicorn + Uvicorn workers
# Usage: gunicorn -c gunicorn.conf.py main:app

import multiprocessing
import os

# ── Server socket ─────────────────────────────────────────────────────────────
bind            = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog         = 2048

# ── Workers ───────────────────────────────────────────────────────────────────
# Use Uvicorn workers for ASGI (FastAPI + WebSocket support)
worker_class    = "uvicorn.workers.UvicornWorker"
workers         = int(os.getenv("WEB_CONCURRENCY", max(2, multiprocessing.cpu_count())))
threads         = 1          # Uvicorn workers are async – 1 thread per worker
worker_connections = 1000

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout         = 120        # /process-frame can take ~1s per frame × batch
keepalive       = 5
graceful_timeout = 30

# ── Logging ───────────────────────────────────────────────────────────────────
loglevel        = os.getenv("LOG_LEVEL", "info")
accesslog       = "-"        # stdout
errorlog        = "-"        # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" %(D)sµs'

# ── Security ──────────────────────────────────────────────────────────────────
limit_request_line   = 4096
limit_request_fields = 100
forwarded_allow_ips  = "*"   # trust X-Forwarded-For behind Cloud Run / nginx

# ── Lifecycle hooks ───────────────────────────────────────────────────────────
def on_starting(server):
    server.log.info("Mentora backend starting (Gunicorn + Uvicorn workers)")

def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} exiting cleanly")

