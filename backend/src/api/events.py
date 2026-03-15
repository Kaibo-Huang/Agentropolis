"""
Event injection endpoint for the Agentropolis simulation.

Endpoint:
  POST /api/sessions/{session_id}/events  — Inject a narrative event into a session

The event designer agent translates free-form narrative into structured
mechanical effects at injection time.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.event_designer import design_event_effects
from src.db import queries
from src.db.engine import get_db

logger = logging.getLogger(__name__)

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
    effects: dict | None = Field(default=None, description="Structured mechanical effects.")
    end_time: str | None = Field(default=None, description="When event effects expire (ISO 8601).")


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

    The event designer agent translates the narrative into structured effects
    that mechanically influence the simulation (happiness, movement, tweets,
    disease, etc.).  Effects are stored alongside the event and applied each
    tick until the event expires.

    - Returns 404 if the session does not exist.
    """
    session = await queries.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    # Default event timestamp to the session's current virtual clock
    event_time: datetime = (
        body.virtual_time if body.virtual_time is not None else session.virtual_time
    )

    # Fetch existing events for world history context
    existing_events = await queries.get_events_for_session(db, session_id)
    existing_prompts = [e.event_prompt for e in existing_events]

    # Call event designer agent to translate narrative → structured effects
    effects = await design_event_effects(
        narrative=body.event_prompt,
        session_id=str(session_id),
        existing_events=existing_prompts if existing_prompts else None,
    )

    # Compute end_time from duration_ticks if the agent set one
    end_time: datetime | None = None
    if effects and effects.get("duration_ticks"):
        end_time = event_time + timedelta(hours=effects["duration_ticks"])

    event = await queries.create_event(
        db,
        session_id=session_id,
        event_prompt=body.event_prompt,
        virtual_time=event_time,
        effects=effects,
        end_time=end_time,
    )

    logger.info(
        "Event %d injected for session %s | effects=%s | end_time=%s",
        event.event_id,
        session_id,
        "yes" if effects else "narrative-only",
        end_time,
    )

    return EventResponse(
        event_id=event.event_id,
        event_prompt=event.event_prompt,
        virtual_time=event.virtual_time.isoformat(),
        session_id=str(session_id),
        effects=effects,
        end_time=end_time.isoformat() if end_time else None,
    )
