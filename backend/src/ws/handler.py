import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.db import queries
from src.db.engine import AsyncSessionLocal
from src.ws.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: UUID):
    # Validate session exists before accepting the connection
    async with AsyncSessionLocal() as db:
        session = await queries.get_session(db, session_id)
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return

    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "subscribe":
                await websocket.send_json(
                    {
                        "type": "subscribed",
                        "data": {"session_id": str(session_id)},
                    }
                )
            elif msg_type == "pong":
                pass  # Heartbeat acknowledgement — nothing to do
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": {"message": f"Unknown message type: {msg_type}"},
                    }
                )
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected from session %s", session_id)
    except Exception as e:
        logger.error("WebSocket error for session %s: %s", session_id, e)
    finally:
        last_client = await manager.disconnect(session_id, websocket)
        if last_client:
            # Auto-pause the simulation when no clients are watching
            async with AsyncSessionLocal() as db:
                await queries.update_session_status(db, session_id, "paused")
                await db.commit()
            logger.info("Session %s auto-paused (last client disconnected)", session_id)
