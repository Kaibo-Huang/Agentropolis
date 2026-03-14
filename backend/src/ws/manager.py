import asyncio
import logging
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per session with heartbeat and backpressure."""

    HEARTBEAT_INTERVAL = 30  # seconds
    HEARTBEAT_TIMEOUT = 90  # seconds
    MAX_BUFFER = 100

    def __init__(self):
        self._connections: dict[UUID, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, session_id: UUID, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections[session_id].append(websocket)
        logger.info("WebSocket connected to session %s", session_id)

    async def disconnect(self, session_id: UUID, websocket: WebSocket) -> bool:
        """Remove websocket from the session pool.

        Returns True when this was the last client for the session (triggers
        auto-pause in the caller).
        """
        async with self._lock:
            if session_id in self._connections:
                try:
                    self._connections[session_id].remove(websocket)
                except ValueError:
                    pass
                if not self._connections[session_id]:
                    del self._connections[session_id]
                    return True  # Last client disconnected — caller should auto-pause
        return False

    async def broadcast(self, session_id: UUID, message: dict):
        """Send a JSON message to all active connections for a session."""
        async with self._lock:
            connections = list(self._connections.get(session_id, []))

        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections without holding the lock during sends
        if dead:
            async with self._lock:
                for ws in dead:
                    try:
                        self._connections[session_id].remove(ws)
                    except (ValueError, KeyError):
                        pass

    def get_connection_count(self, session_id: UUID) -> int:
        return len(self._connections.get(session_id, []))

    async def start_heartbeat(self):
        """Start the background heartbeat task."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket heartbeat started (interval=%ds)", self.HEARTBEAT_INTERVAL)

    async def stop_heartbeat(self):
        """Cancel and await the heartbeat task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        logger.info("WebSocket heartbeat stopped")

    async def _heartbeat_loop(self):
        while True:
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

            async with self._lock:
                all_sessions = list(self._connections.items())

            for session_id, connections in all_sessions:
                dead: list[WebSocket] = []
                for ws in connections:
                    try:
                        await ws.send_json({"type": "ping"})
                    except Exception:
                        dead.append(ws)

                if dead:
                    async with self._lock:
                        for ws in dead:
                            try:
                                self._connections[session_id].remove(ws)
                            except (ValueError, KeyError):
                                pass


# Module-level singleton used by both handler.py and any agent that broadcasts
manager = ConnectionManager()
