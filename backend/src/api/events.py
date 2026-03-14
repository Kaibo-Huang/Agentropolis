"""
Event injection endpoint for the Agentropolis simulation.

Endpoint:
  POST /api/sessions/{session_id}/events  — Inject a narrative event into a session
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.db import queries

router = APIRouter(prefix="/sessions/{session_id}", tags=["events"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class InjectEventRequest(BaseModel):
    event_prompt: str = Field(
        max_length=1000,
        description="Narrative description of the event to inject (max 1000 characters).",
    )
    virtual_time: datetime | None = Field(
        default=None,
        description=(
            "In-simulation timestamp for the event. "
            "Defaults to the session's current virtual_time when omitted."
        ),
    )


class EventResponse(BaseModel):
    event_id: int = Field(description="Session-scoped sequential event identifier.")
    event_prompt: str = Field(description="The injected event description.")
    virtual_time: str = Field(description="Event's in-simulation timestamp (ISO 8601).")
    session_id: str = Field(description="UUID of the owning session.")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inject a narrative event into a session",
)
async def inject_event(
    session_id: UUID,
    body: InjectEventRequest,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """
    Persist a new narrative event associated with `session_id`.

    The event is stored at `virtual_time` (or the session's current virtual
    clock if omitted) and will be available to the tick orchestrator on the
    next simulation step.

    - Returns 404 if the session does not exist.
    """
    session = await queries.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    # Default event timestamp to the session's current virtual clock
    event_time: datetime = body.virtual_time if body.virtual_time is not None else session.virtual_time

    event = await queries.create_event(
        db,
        session_id=session_id,
        event_prompt=body.event_prompt,
        virtual_time=event_time,
    )

    return EventResponse(
        event_id=event.event_id,
        event_prompt=event.event_prompt,
        virtual_time=event.virtual_time.isoformat(),
        session_id=str(session_id),
    )
