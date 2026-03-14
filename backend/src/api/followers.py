from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import queries
from src.db.engine import get_db

router = APIRouter(prefix="/sessions/{session_id}", tags=["followers"])


class FollowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    follower_id: int
    archetype_id: int
    name: str
    age: int | None
    gender: str | None
    race: str | None
    home_position: list | dict | None
    work_position: list | dict | None
    position: list | dict | None
    status_ailments: list | None
    happiness: float
    volatility: float


class FollowerListResponse(BaseModel):
    followers: list[FollowerResponse]
    total: int
    offset: int
    limit: int


@router.get("/followers", response_model=FollowerListResponse)
async def list_followers(
    session_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    followers = await queries.get_followers_for_session(db, session_id, offset, limit)
    total = await queries.get_follower_count(db, session_id)

    return FollowerListResponse(
        followers=[FollowerResponse.model_validate(f) for f in followers],
        total=total,
        offset=offset,
        limit=limit,
    )
