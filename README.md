#  Mentora – Cognitive Fatigue & Well-Being Tracker

> Real-time, privacy-safe AI system that detects fatigue and stress using webcam-based facial analysis, providing insights, chatbot support, and deep analytics.

---

##  Architecture

```
Webcam → OpenCV → MediaPipe → Feature Extraction (EAR/MAR)
      → CNN-LSTM Model → FastAPI → Supabase
      → React UI (Dashboard · Monitoring · Reports · Chatbot)
```

---

##  Project Structure

```
mentora/
├── ai_model/
│   ├── fatigue_detector.py     # MediaPipe + EAR/MAR feature extraction
│   ├── cnn_lstm_model.py       # CNN-LSTM TensorFlow model
│   ├── requirements.txt
│   └── weights/                # Trained model weights (auto-created)
│
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── routers/
│   │   ├── session.py          # POST /start-session, /end-session
│   │   ├── frames.py           # POST /process-frame
│   │   ├── reports.py          # GET /report, GET /reports/weekly
│   │   ├── chatbot.py          # POST /chatbot
│   │   └── websocket_router.py # WS /ws/{session_id}
│   ├── services/
│   │   ├── supabase_service.py # Supabase database operations
│   │   ├── auth_service.py     # Supabase token verification
│   │   ├── detector_service.py # Per-session detector pool
│   │   ├── connection_manager.py # WebSocket manager
│   │   └── report_service.py   # PDF generation (ReportLab)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Router + providers
│   │   ├── pages/
│   │   │   ├── Login.jsx       # Supabase Auth login
│   │   │   ├── Register.jsx    # Supabase Auth register
│   │   │   ├── Dashboard.jsx   # Live score + charts + Pomodoro
│   │   │   ├── Monitoring.jsx  # Webcam + real-time AI output
│   │   │   ├── Reports.jsx     # Analytics + PDF export
│   │   │   └── ChatbotPage.jsx # AI wellness chatbot
│   │   ├── components/
│   │   │   ├── ui/AppLayout.jsx          # Sidebar layout
│   │   │   ├── ui/LoadingScreen.jsx
│   │   │   └── dashboard/
│   │   │       ├── FatigueGauge.jsx      # Animated SVG gauge
│   │   │       └── PomodoroTimer.jsx     # Pomodoro with ring
│   │   ├── context/
│   │   │   ├── AuthContext.jsx   # Supabase auth state
│   │   │   ├── ThemeContext.jsx  # Dark/light mode
│   │   │   └── SessionContext.jsx # Session + frame state
│   │   ├── hooks/
│   │   │   ├── useWebcam.js     # Webcam stream + frame capture
│   │   │   └── usePomodoro.js   # Pomodoro timer logic
│   │   └── utils/
│   │       ├── api.js           # Axios instance with auth
│   │       └── supabaseClient.js   # Supabase client init
│   ├── package.json
│   ├── tailwind.config.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
│
├── docker-compose.yml           # Full-stack Docker deployment
└── README.md
```

---

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- A Supabase project
- Webcam

---

### 1. Configure Supabase

1. Create a Supabase project at https://supabase.com/dashboard`r`n2. Enable **Authentication** ? Email/Password`r`n3. Create the required database tables and Row Level Security policies`r`n4. Copy the Supabase project URL and publishable key into the frontend `.env.local` file

---

### 2. Backend Setup

```bash
cd backend

# Copy and fill environment variables
cp .env.example .env
# Edit .env:
#   GEMINI_API_KEY=your-gemini-api-key   (optional – chatbot works without it)
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --port 8000
```

Backend available at: **http://localhost:8000**
API docs (Swagger): **http://localhost:8000/docs**

---

### 3. Frontend Setup

```bash
cd frontend

# Copy and fill environment variables
cp .env.example .env
# Edit the frontend `.env.local` with your Supabase configuration values

# Install dependencies
npm install --legacy-peer-deps

# Start dev server
npm start
```

Frontend available at: **http://localhost:3000**

---

### 4. Docker Deployment (Production)

```bash
# From project root
cp backend/.env.example backend/.env     # fill values
cp frontend/.env.example frontend/.env   # fill values

docker-compose up --build -d

# View logs
docker-compose logs -f
```

---

##  API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/start-session` | Create a new monitoring session |
| `POST` | `/api/v1/process-frame` | Send base64 JPEG frame for AI analysis |
| `POST` | `/api/v1/end-session` | End and finalise a session |
| `GET`  | `/api/v1/report?session_id=&format=json\|pdf` | Get full session report |
| `GET`  | `/api/v1/reports/weekly` | Get 7-day aggregated analytics |
| `POST` | `/api/v1/chatbot` | AI wellness chatbot query |

### WebSocket

```
ws://localhost:8000/ws/{session_id}
```

Send `{"type": "ping"}` → receives `{"type": "pong"}`

### Authentication

All endpoints require `Authorization: Bearer <supabase-access-token>` header.
The frontend handles this automatically via the Axios interceptor.

---

##  AI Model Details

### Feature Extraction (MediaPipe)

| Feature | Formula | Normal Range | Fatigue Threshold |
|---------|---------|-------------|-------------------|
| **EAR** (Eye Aspect Ratio) | `(A+B) / (2×C)` | > 0.22 | < 0.20 |
| **MAR** (Mouth Aspect Ratio) | `(A+B) / (2×C)` | < 0.50 | > 0.65 |

### CNN-LSTM Architecture

```
Input (30 frames × 6 features)
  → Conv1D(64, k=3, ReLU) + BN
  → Conv1D(128, k=3, ReLU) + BN + MaxPool + Dropout(0.3)
  → LSTM(128, return_sequences=True)
  → LSTM(64)
  → Dense(64, ReLU) + BN + Dropout(0.3)
  → Dense(3, Softmax)  → [Normal, Stressed, Fatigued]
```

### Fatigue Score (0–100)

Weighted combination of:
- **45%** Eye droopiness (EAR drop from baseline)
- **25%** Abnormal blink rate (normal: 15–20/min)
- **20%** Yawn frequency
- **10%** Sustained mouth openness (MAR)

---

## Supabase Database Schema

```
users/
  {uid}/
    email, displayName, createdAt, preferences

sessions/
  {sessionId}/
    user_id, started_at, ended_at, status,
    avg_fatigue, peak_fatigue, frame_count
    fatigue_data/
      {entryId}/
        timestamp, fatigue_score, state, ear, mar,
        blink_count, yawn_count

reports/
  {reportId}/
    user_id, session_id, generated_at, analytics
```

---

##  Push Notifications

Push notifications are currently disabled in Mentora.
---

##  Training the CNN-LSTM Model

```python
# backend/train_model.py (example)
from ai_model.cnn_lstm_model import FatigueModel
import numpy as np

model = FatigueModel()

# X: shape (N, 30, 6) – sequences of [ear, mar, blink_rate, yawn_rate, pitch, yaw]
# y: shape (N,)       – labels 0=Normal, 1=Stressed, 2=Fatigued
X = np.load("data/sequences.npy")
y = np.load("data/labels.npy")

model.train(X, y, epochs=30, batch_size=64)
# Weights saved to ai_model/weights/cnn_lstm_v1.h5
```

---

##  Privacy & Security

- **No video stored** – frames are decoded in-memory and immediately discarded
- **No raw images in Supabase** – only numeric metrics (EAR, MAR, scores)
- **Supabase Auth** – all API endpoints require a valid JWT
- **Supabase Row Level Security (RLS)** – users can only access their own data
- **HTTPS enforced** in production via nginx

---

##  Deployment Checklist

- [ ] Set `ENV=production` in backend `.env`
- [ ] Configure `CORS_ORIGINS` to your production domain
- [ ] Configure Supabase Row Level Security policies
- [ ] Create required Supabase database indexes
- [ ] Configure production security policies
- [ ] Push notifications are currently disabled`r`n- [ ] Configure a custom domain in Vercel (optional)

---

##  Tech Stack

| Layer | Technology |
|-------|-----------|
| AI / CV | Python, OpenCV, MediaPipe, TensorFlow/Keras |
| Backend | FastAPI, Uvicorn, WebSockets |
| Auth/DB | Supabase Auth, Supabase PostgreSQL |
| Notifications | Push notifications (currently disabled) |
| Chatbot | Gemini 2.5 Flash (+ rule-based fallback) |
| Frontend | React 18, Tailwind CSS, Recharts |
| PDF | ReportLab |
| DevOps | Docker, Docker Compose, nginx |

---














