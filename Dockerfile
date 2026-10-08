FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgles2 \
    libegl1 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY ai_model /app/ai_model

RUN mkdir -p /app/ai_model/weights && \
    curl -fsSL -o /app/ai_model/weights/face_landmarker.task \
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"

CMD ["sh", "-c", "gunicorn backend.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:10000 --workers 1 --timeout 120"]
CMD ["sh", "-c", "cd /app/backend && gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:10000 --workers 1 --timeout 120"]

