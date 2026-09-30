"""Mentora – WebSocket Connection Manager"""

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        self.active.setdefault(session_id, []).append(ws)

    def disconnect(self, ws: WebSocket, session_id: str):
        if session_id in self.active:
            self.active[session_id] = [w for w in self.active[session_id] if w != ws]

    async def broadcast(self, session_id: str, data: dict):
        dead = []
        for ws in self.active.get(session_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, session_id)

