"""
Reusable async query functions for Agentropolis.

All functions accept an AsyncSession as their first argument and return
model instances or plain dicts.  Raw Row objects are never exposed to callers.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Archetype,
    Company,
    Demographic,
    Event,
    Follower,
    Location,
    Memory,
    Post,
    Relationship,
    Session,
)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
    result = await db.execute(
        select(Session).where(Session.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession,
    config: dict | None = None,
    virtual_time: datetime | None = None,
) -> Session:
    from datetime import timezone

    vt = virtual_time or datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
    session = Session(config=config, virtual_time=vt)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def update_session_status(
    db: AsyncSession, session_id: uuid.UUID, status: str
) -> Session | None:
    await db.execute(
        update(Session)
        .where(Session.session_id == session_id)
        .values(status=status)
    )
    return await get_session(db, session_id)


async def update_session_virtual_time(
    db: AsyncSession, session_id: uuid.UUID, virtual_time: datetime
) -> Session | None:
    await db.execute(
        update(Session)
        .where(Session.session_id == session_id)
        .values(virtual_time=virtual_time)
    )
    return await get_session(db, session_id)


async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
    result = await db.execute(
        delete(Session).where(Session.session_id == session_id)
    )
    return result.rowcount > 0


# ---------------------------------------------------------------------------
# Archetypes
# ---------------------------------------------------------------------------


async def get_archetypes_for_session(
    db: AsyncSession, session_id: uuid.UUID
) -> list[Archetype]:
    result = await db.execute(
        select(Archetype).where(Archetype.session_id == session_id)
    )
    return list(result.scalars().all())


async def batch_insert_archetypes(
    db: AsyncSession, archetypes_data: list[dict]
) -> None:
    if not archetypes_data:
        return
    await db.execute(insert(Archetype), archetypes_data)


# ---------------------------------------------------------------------------
# Followers
# ---------------------------------------------------------------------------


async def get_followers_by_archetype(
    db: AsyncSession, session_id: uuid.UUID, archetype_id: int
) -> list[Follower]:
    result = await db.execute(
        select(Follower).where(
            Follower.session_id == session_id,
            Follower.archetype_id == archetype_id,
        )
    )
    return list(result.scalars().all())


async def get_followers_for_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    offset: int = 0,
    limit: int = 100,
) -> list[Follower]:
    result = await db.execute(
        select(Follower)
        .where(Follower.session_id == session_id)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_follower_count(db: AsyncSession, session_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).where(Follower.session_id == session_id).select_from(Follower)
    )
    return result.scalar_one()


async def batch_insert_followers(
    db: AsyncSession, followers_data: list[dict]
) -> None:
    if not followers_data:
        return
    await db.execute(insert(Follower), followers_data)


async def create_follower(
    db: AsyncSession, session_id: uuid.UUID, follower_data: dict
) -> Follower:
    """Insert a single follower; follower_id is assigned as next id for session."""
    next_id = await get_max_id(db, Follower, session_id, "follower_id")
    follower_data["session_id"] = session_id
    follower_data["follower_id"] = next_id
    row = Follower(**follower_data)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def batch_update_followers(
    db: AsyncSession, updates: list[dict]
) -> None:
    """
    Each dict in `updates` must contain `session_id` and `follower_id`
    (to identify the row) plus the columns to update.
    Executed as individual UPDATE statements to preserve per-row values.
    """
    for upd in updates:
        sid = upd.pop("session_id")
        fid = upd.pop("follower_id")
        if upd:
            await db.execute(
                update(Follower)
                .where(
                    Follower.session_id == sid,
                    Follower.follower_id == fid,
                )
                .values(**upd)
            )


async def get_follower_stats(
    db: AsyncSession, session_id: uuid.UUID, archetype_id: int
) -> dict:
    """
    Returns aggregate stats for followers of a given archetype:
      count, avg_happiness, min_happiness, max_happiness
    """
    result = await db.execute(
        select(
            func.count().label("count"),
            func.avg(Follower.happiness).label("avg_happiness"),
            func.min(Follower.happiness).label("min_happiness"),
            func.max(Follower.happiness).label("max_happiness"),
        ).where(
            Follower.session_id == session_id,
            Follower.archetype_id == archetype_id,
        )
    )
    row = result.mappings().one()
    return dict(row)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


async def batch_insert_companies(
    db: AsyncSession, companies_data: list[dict]
) -> None:
    if not companies_data:
        return
    await db.execute(insert(Company), companies_data)


# ---------------------------------------------------------------------------
# Memories
# ---------------------------------------------------------------------------


async def get_recent_memories(
    db: AsyncSession,
    session_id: uuid.UUID,
    archetype_id: int,
    limit: int = 20,
) -> list[Memory]:
    result = await db.execute(
        select(Memory)
        .where(
            Memory.session_id == session_id,
            Memory.archetype_id == archetype_id,
        )
        .order_by(Memory.virtual_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def batch_insert_memories(
    db: AsyncSession, memories_data: list[dict]
) -> None:
    if not memories_data:
        return
    await db.execute(insert(Memory), memories_data)


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------


async def create_post(db: AsyncSession, post_data: dict) -> Post:
    post = Post(**post_data)
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return post


async def get_posts_for_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
) -> list[Post]:
    result = await db.execute(
        select(Post)
        .where(Post.session_id == session_id)
        .order_by(Post.virtual_time.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


async def get_events_for_session(
    db: AsyncSession, session_id: uuid.UUID
) -> list[Event]:
    result = await db.execute(
        select(Event)
        .where(Event.session_id == session_id)
        .order_by(Event.virtual_time)
    )
    return list(result.scalars().all())


async def create_event(
    db: AsyncSession,
    session_id: uuid.UUID,
    event_prompt: str,
    virtual_time: datetime,
) -> Event:
    # Determine next event_id for this session
    next_id = await get_max_id(db, Event, session_id, "event_id")
    event = Event(
        session_id=session_id,
        event_id=next_id,
        event_prompt=event_prompt,
        virtual_time=virtual_time,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


async def batch_insert_relationships(
    db: AsyncSession, relationships_data: list[dict]
) -> None:
    if not relationships_data:
        return
    await db.execute(insert(Relationship), relationships_data)


async def get_relationship_summary(
    db: AsyncSession, session_id: uuid.UUID, archetype_id: int
) -> dict:
    """
    Returns the count and average strength of relationships for followers
    belonging to the given archetype in a session.

    Uses a subquery to find relevant follower IDs first.
    """
    follower_ids_subq = (
        select(Follower.follower_id)
        .where(
            Follower.session_id == session_id,
            Follower.archetype_id == archetype_id,
        )
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            func.count().label("relationship_count"),
            func.avg(Relationship.relation_strength).label("avg_strength"),
            func.min(Relationship.relation_strength).label("min_strength"),
            func.max(Relationship.relation_strength).label("max_strength"),
        ).where(
            Relationship.session_id == session_id,
            (Relationship.follower1_id.in_(follower_ids_subq))
            | (Relationship.follower2_id.in_(follower_ids_subq)),
        )
    )
    row = result.mappings().one()
    return dict(row)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------


async def get_locations_by_region(
    db: AsyncSession,
    region: str,
    location_type: str | None = None,
) -> list[Location]:
    stmt = select(Location).where(Location.region == region)
    if location_type is not None:
        stmt = stmt.where(Location.type == location_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


async def get_max_id(
    db: AsyncSession,
    model_class: Any,
    session_id: uuid.UUID,
    id_column: str,
) -> int:
    """
    Returns the next sequential integer ID for a session-scoped entity.
    Starts at 1 if no rows exist yet.
    """
    col = getattr(model_class, id_column)
    result = await db.execute(
        select(func.max(col)).where(
            model_class.session_id == session_id  # type: ignore[attr-defined]
        )
    )
    current_max = result.scalar_one_or_none()
    return (current_max or 0) + 1
