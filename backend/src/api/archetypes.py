from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import queries
from src.db.engine import get_db

router = APIRouter(prefix="/sessions/{session_id}", tags=["archetypes"])


class ArchetypeResponse(BaseModel):
    archetype_id: int
    industry: str
    social_class: str | None
    region: str
    home_neighborhood: str | None = None
    work_district: str | None = None
    follower_count: int


class ArchetypeListResponse(BaseModel):
    archetypes: list[ArchetypeResponse]


@router.get("/archetypes", response_model=ArchetypeListResponse)
async def list_archetypes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rows = await queries.get_archetypes_with_follower_counts(db, session_id)

    result = [
        ArchetypeResponse(
            archetype_id=arch.archetype_id,
            industry=arch.industry,
            social_class=arch.social_class,
            region=arch.region,
            home_neighborhood=getattr(arch, "home_neighborhood", None),
            work_district=getattr(arch, "work_district", None),
            follower_count=count,
        )
        for arch, count in rows
    ]

    return ArchetypeListResponse(archetypes=result)
