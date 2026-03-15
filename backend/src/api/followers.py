from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.avatar.schema import AvatarParams
from src.db import queries
from src.db.engine import get_db

router = APIRouter(prefix="/sessions/{session_id}", tags=["followers"])

# Default position (Downtown Toronto) for new custom-avatar followers
_DEFAULT_POSITION = [43.6510, -79.3832]


class FollowerMemoryResponse(BaseModel):
    virtual_time: datetime
    action_type: str
    thinking: str


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
    avatar_seed: int | None = None
    avatar_params: dict | None = None
    industry: str | None = None
    home_neighborhood: str | None = None
    work_district: str | None = None
    recent_memories: list[FollowerMemoryResponse] = Field(default_factory=list)


class FollowerListResponse(BaseModel):
    followers: list[FollowerResponse]
    total: int
    offset: int
    limit: int


class CreateFollowerRequest(BaseModel):
    """Create a follower with a custom avatar (e.g. user joining the simulation)."""

    name: str = "You"
    avatar_params: AvatarParams


@router.get("/followers", response_model=FollowerListResponse)
async def list_followers(
    session_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    followers = await queries.get_followers_for_session(db, session_id, offset, limit)
    archetype_ids = sorted({f.archetype_id for f in followers})
    archetypes = await queries.get_archetypes_for_session(db, session_id)
    industry_by_archetype = {a.archetype_id: a.industry for a in archetypes}
    recent_memories_by_archetype = await queries.get_recent_memory_summaries_for_archetypes(
        db,
        session_id,
        archetype_ids,
        limit_per_archetype=3,
    )
    for follower in followers:
        setattr(
            follower,
            "recent_memories",
            recent_memories_by_archetype.get(follower.archetype_id, []),
        )
        setattr(
            follower,
            "industry",
            industry_by_archetype.get(follower.archetype_id),
        )
    total = await queries.get_follower_count(db, session_id)

    return FollowerListResponse(
        followers=[FollowerResponse.model_validate(f) for f in followers],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/followers", response_model=FollowerResponse)
async def create_follower_with_avatar(
    session_id: UUID,
    body: CreateFollowerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new follower with a custom avatar (avatar_seed null, avatar_params set)."""
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    archetypes = await queries.get_archetypes_for_session(db, session_id)
    if not archetypes:
        raise HTTPException(
            status_code=400,
            detail="Session has no archetypes; create a session first.",
        )
    archetype_id = archetypes[0].archetype_id

    follower_data = {
        "archetype_id": archetype_id,
        "name": body.name[:128],
        "age": None,
        "gender": None,
        "race": None,
        "home_position": _DEFAULT_POSITION,
        "work_position": _DEFAULT_POSITION,
        "position": _DEFAULT_POSITION,
        "status_ailments": [],
        "happiness": 0.5,
        "volatility": 0.5,
        "avatar_seed": None,
        "avatar_params": body.avatar_params.model_dump(),
    }
    follower = await queries.create_follower(db, session_id, follower_data)
    await db.commit()
    await db.refresh(follower)
    return FollowerResponse.model_validate(follower)
