"""
Session CRUD endpoints for the Agentropolis API.

Endpoints:
  POST   /api/sessions                        — Create a new session
  GET    /api/sessions/{session_id}           — Get session state
  DELETE /api/sessions/{session_id}           — Delete session (cascade)
  POST   /api/sessions/{session_id}/resume    — Resume a paused session
  POST   /api/sessions/{session_id}/pause     — Pause a running session
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.db.queries import (
    create_session,
    delete_session,
    get_follower_count,
    get_session,
    update_session_status,
)

# ---------------------------------------------------------------------------
# Optional seeder import — skip gracefully if the module does not exist yet
# ---------------------------------------------------------------------------

try:
    from src.simulation.seeder import seed_session as _seed_session  # type: ignore[import]

    _SEEDER_AVAILABLE = True
except ImportError:
    _SEEDER_AVAILABLE = False


router = APIRouter(prefix="/sessions", tags=["sessions"])

# ---------------------------------------------------------------------------
# Default virtual-time for new sessions (current Toronto time, rounded down to the hour)
# ---------------------------------------------------------------------------

TORONTO_TZ = ZoneInfo("America/Toronto")


def _default_virtual_time() -> datetime:
    now = datetime.now(TORONTO_TZ)
    return now.replace(minute=0, second=0, microsecond=0)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SessionConfig(BaseModel):
    """Validated simulation configuration embedded in a session."""

    total_population: int = Field(
        default=500,
        ge=500,
        le=5_000,
        description="Total number of follower agents to simulate (500–5,000).",
    )
    archetype_count: int = Field(
        default=20,
        ge=1,
        le=1_000,
        description="Number of distinct follower archetypes (1–1,000).",
    )

    model_config = ConfigDict(extra="allow")


class CreateSessionRequest(BaseModel):
    """Request body for POST /sessions."""

    config: SessionConfig | None = Field(
        default=None,
        description="Optional simulation configuration. Defaults are applied for omitted fields.",
    )


class SessionResponse(BaseModel):
    """Response body returned for all session operations."""

    session_id: str = Field(description="Unique session identifier (UUID).")
    created_at: datetime = Field(description="Wall-clock time the session was created.")
    virtual_time: datetime = Field(description="Current in-simulation timestamp.")
    status: str = Field(description="Session lifecycle status: 'paused' or 'running'.")
    config: dict[str, Any] | None = Field(
        default=None,
        description="Simulation configuration as stored.",
    )
    follower_count: int = Field(
        default=0,
        description="Number of follower agents currently seeded for this session.",
    )

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_session_or_404(db: AsyncSession, session_id: uuid.UUID):
    """Return the Session ORM object or raise 404."""
    session_obj = await get_session(db, session_id)
    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return session_obj


async def _build_response(db: AsyncSession, session_obj) -> SessionResponse:
    """Construct a SessionResponse, including the live follower count."""
    follower_count = await get_follower_count(db, session_obj.session_id)
    return SessionResponse(
        session_id=str(session_obj.session_id),
        created_at=session_obj.created_at,
        virtual_time=session_obj.virtual_time,
        status=session_obj.status,
        config=session_obj.config,
        follower_count=follower_count,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new simulation session",
)
async def create_session_endpoint(
    body: CreateSessionRequest = CreateSessionRequest(),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Create a new session with status 'paused' and virtual_time set to the
    current Toronto time (rounded down to the hour).

    If the simulation seeder module is available it will be invoked to
    populate archetypes, followers, and companies according to `config`.
    """
    # Resolve config — fall back to defaults if nothing was provided
    cfg: SessionConfig = body.config or SessionConfig()
    config_dict = cfg.model_dump()

    # Persist the session row with virtual_time = current time (hour boundary)
    session_obj = await create_session(
        db, config=config_dict, virtual_time=_default_virtual_time()
    )

    # Invoke seeder when available
    if _SEEDER_AVAILABLE:
        await _seed_session(db, session_obj, config_dict)  # type: ignore[name-defined]

    return await _build_response(db, session_obj)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session state",
)
async def get_session_endpoint(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Return the current state and metadata for a session."""
    session_obj = await _get_session_or_404(db, session_id)
    return await _build_response(db, session_obj)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session (cascades to all child entities)",
)
async def delete_session_endpoint(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a session and all associated data (followers,
    archetypes, companies, posts, events, memories, relationships).
    Returns 404 if the session does not exist.
    """
    deleted = await delete_session(db, session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )


@router.post(
    "/{session_id}/resume",
    response_model=SessionResponse,
    summary="Resume a paused session",
)
async def resume_session_endpoint(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Transition a session from 'paused' to 'running'.
    Returns 409 if the session is already running.
    """
    session_obj = await _get_session_or_404(db, session_id)
    if session_obj.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session '{session_id}' is already running.",
        )
    updated = await update_session_status(db, session_id, "running")
    return await _build_response(db, updated)


@router.post(
    "/{session_id}/pause",
    response_model=SessionResponse,
    summary="Pause a running session",
)
async def pause_session_endpoint(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Transition a session from 'running' to 'paused'.
    Returns 409 if the session is already paused.
    """
    session_obj = await _get_session_or_404(db, session_id)
    if session_obj.status == "paused":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session '{session_id}' is already paused.",
        )
    updated = await update_session_status(db, session_id, "paused")
    return await _build_response(db, updated)
