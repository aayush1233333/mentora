# Mentora – Deployment Guide

## Current Architecture

- Frontend: Vercel
- Backend: Render
- Authentication: Supabase Auth
- Database: Supabase PostgreSQL
- AI/ML: TensorFlow + MediaPipe + OpenCV
- API: FastAPI
- WebSocket: FastAPI WebSocket
- Optional chatbot: OpenAI API

---

## 1. Backend Deployment – Render

Backend directory:

``text
backend/
`` 

### Build Command

``bash
pip install -r requirements.txt
`` 

### Start Command

``bash
uvicorn main:app --host 0.0.0.0 --port $PORT
`` 

### Required Backend Environment Variables

``text
ENV=production
SUPABASE_URL=<your-supabase-project-url>
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>
CORS_ORIGINS=https://mentora-repoo.vercel.app
OPENAI_API_KEY=<optional>
`` 

Do not commit .env or any service-role key to Git.

---

## 2. Frontend Deployment – Vercel

Frontend directory:

frontend/

### Build Command

``bash
npm install
npm run build
`` 

### Required Frontend Environment Variables

``text
REACT_APP_SUPABASE_URL=<your-supabase-project-url>
REACT_APP_SUPABASE_PUBLISHABLE_KEY=<your-supabase-publishable-key>
REACT_APP_API_URL=<your-render-backend-url>/api/v1
REACT_APP_WS_URL=<your-render-backend-url>
`` 

For production WebSocket connections, use wss://.

---

## 3. Supabase Configuration

Supabase provides:

- Email/password authentication
- User profiles
- Session records
- Fatigue entries
- Row Level Security (RLS)

Required tables:

``text
profiles
sessions
fatigue_entries
`` 

RLS policies ensure authenticated users can access only their own data.

---

## 4. WebSocket

Mentora uses FastAPI WebSockets for real-time monitoring.

Production frontend configuration:

``text
wss://your-backend.onrender.com
`` 

The backend authenticates WebSocket connections using the Supabase access token.

---

## 5. Production Checklist

### Supabase

- [ ] Create Supabase project
- [ ] Enable Email/Password authentication
- [ ] Create profiles table
- [ ] Create sessions table
- [ ] Create atigue_entries table
- [ ] Enable RLS
- [ ] Configure RLS policies

### Render

- [ ] Deploy backend
- [ ] Configure SUPABASE_URL`r
- [ ] Configure SUPABASE_SERVICE_ROLE_KEY`r
- [ ] Configure CORS_ORIGINS`r
- [ ] Configure OPENAI_API_KEY if chatbot requires it
- [ ] Confirm /health returns ok`r

### Vercel

- [ ] Deploy frontend
- [ ] Configure Supabase environment variables
- [ ] Configure REACT_APP_API_URL`r
- [ ] Configure REACT_APP_WS_URL`r
- [ ] Confirm login works
- [ ] Confirm dashboard works
- [ ] Confirm monitoring works
- [ ] Confirm reports work

---

## 6. Security

Never commit:

``text
.env
.env.local
service-role keysAPI keys
private credentials
`` 

The Supabase publishable key may be used by the frontend.

The Supabase service-role key must remain on the backend and must never be exposed to the browser.

---

## 7. Current Deployment

Frontend:

``text
https://mentora-repoo.vercel.app
`` 

Backend:

``text
Render deployment URL
`` 

Supabase:

``text
Supabase project
``

