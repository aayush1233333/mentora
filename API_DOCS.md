# Mentora API – Complete Reference v1.0

Base URL: `http://localhost:8000/api/v1`
Auth header (all endpoints): `Authorization: Bearer <supabase-access-token>`
Swagger UI: `http://localhost:8000/docs`

---

## Sessions

### POST /start-session
### POST /end-session
### GET /sessions          — paginated list (newest first)
### GET /sessions/{id}     — single session
### DELETE /sessions/{id}  — delete session + all sub-collection data

## Frames

### POST /process-frame
Returns: fatigue_score, state, ear, mar, blink_count, yawn_count, head_pitch, head_yaw, landmarks_detected

## Reports

### GET /report?session_id=&format=json|pdf
### GET /reports/weekly    — 7-day aggregate

## Chatbot

### POST /chatbot
Params: message, fatigue_score, state, history[]
Returns: reply (OpenAI GPT-4o-mini + rule-based fallback)

## User

### GET /user/preferences
### PUT /user/preferences

## Wellness

### GET /wellness/tip?state=Stressed&score=52   — single contextual tip
### GET /wellness/tips?state=Fatigued&n=3       — batch of tips

## WebSocket

ws://localhost:8000/ws/{session_id}

## Rate Limits

/process-frame: 10 req/s burst, 5 req/s sustained
/chatbot:        5 req/s burst, 1 req/s sustained

## Error codes: 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Invalid, 429 Rate Limited, 500 Server Error

