from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import queries
from src.db.engine import get_db

router = APIRouter(prefix="/sessions/{session_id}", tags=["posts"])


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int
    follower_id: int
    text: str
    virtual_time: datetime
    created_at: datetime | None


class PostListResponse(BaseModel):
    posts: list[PostResponse]
    offset: int
    limit: int


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    session_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    posts = await queries.get_posts_for_session(db, session_id, offset, limit)

    return PostListResponse(
        posts=[PostResponse.model_validate(p) for p in posts],
        offset=offset,
        limit=limit,
    )
