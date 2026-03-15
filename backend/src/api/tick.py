"""
Tick advancement endpoint for the Agentropolis simulation.

Endpoint:
  POST /api/sessions/{session_id}/tick  — Advance virtual time and run simulation tick
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.db import queries

router = APIRouter(prefix="/sessions/{session_id}", tags=["simulation"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TickRequest(BaseModel):
    target_time: datetime = Field(description="Target virtual time to advance to")


class TickResponse(BaseModel):
    tick_number: int = Field(description="Sequential tick number (hours elapsed)")
    virtual_time: str = Field(description="New virtual time after the tick (ISO 8601)")
    archetypes_processed: int = Field(description="Number of archetypes successfully processed")
    archetypes_failed: int = Field(description="Number of archetypes that failed during the tick")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/tick",
    response_model=TickResponse,
    status_code=status.HTTP_200_OK,
    summary="Advance the simulation by one tick",
)
async def advance_tick(
    session_id: UUID,
    body: TickRequest,
    db: AsyncSession = Depends(get_db),
) -> TickResponse:
    """
    Advance the session's virtual clock to `target_time` and run the hourly
    tick orchestrator for all archetypes.

    - Returns 404 if the session does not exist.
    - Returns 409 if the session is not in 'running' state.
    - Returns 400 if `target_time` is not strictly after the current virtual_time.
    - Returns 501 if the tick orchestrator module has not been implemented yet.

    If the tick crosses a calendar day boundary the health tick is also run
    (silently skipped when that module is not available).
    """
    session = await queries.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    if session.status != "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session must be running to advance tick.",
        )

    # Validate monotonic virtual time
    if body.target_time <= session.virtual_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"target_time must be strictly after the current virtual_time "
                f"({session.virtual_time.isoformat()})."
            ),
        )

    # Lazy import — tick orchestrator may not exist during early development
    try:
        from src.simulation.tick_orchestrator import run_hourly_tick  # type: ignore[import]
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Tick orchestrator not implemented yet.",
        )

    # Tick number = number of full hours being advanced (minimum 1)
    tick_number = max(
        1,
        int((body.target_time - session.virtual_time).total_seconds() / 3600),
    )

    # Detect calendar-day boundary crossing (triggers health tick)
    crosses_day = session.virtual_time.date() != body.target_time.date()

    result: dict = await run_hourly_tick(
        session_id=session_id,
        target_time=body.target_time,
        tick_number=tick_number,
    )

    # Optional health tick on day boundary
    if crosses_day:
        try:
            from src.simulation.health_tick import run_health_tick  # type: ignore[import]

            disease_mult = result.get("disease_transmission_multiplier", 1.0)
            health_result = await run_health_tick(session_id, disease_multiplier=disease_mult)
            result["health_updates"] = health_result
        except ImportError:
            pass  # health_tick module not available yet — safe to skip

    return TickResponse(**result)
