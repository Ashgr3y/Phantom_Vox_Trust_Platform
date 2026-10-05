from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class SessionHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[session_id].add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[session_id].discard(websocket)
            if not self._connections[session_id]:
                self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, payload: dict) -> None:
        async with self._lock:
            sockets = list(self._connections.get(session_id, set()))
        stale: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        if stale:
            async with self._lock:
                for websocket in stale:
                    self._connections[session_id].discard(websocket)


session_hub = SessionHub()
