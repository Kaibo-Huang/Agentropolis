"""
Railtracks function_node tools for the archetype (Tier 1) agent.

Each tool queries the database using shared context injected via rt.context.
The archetype agent autonomously decides which tools to call (up to 10 per tick).

Context keys expected (injected by tick_orchestrator before rt.call):
    session_id   (uuid.UUID)  — current simulation session
    archetype_id (int)        — archetype being processed
    region       (str)        — archetype's geographic region
    db_session   (AsyncSession) — active database session
    virtual_time (str)        — current virtual time ISO string
    actions_finish_at (str)   — when previous actions finish ISO string
    next_tick_time    (str)   — next tick target time ISO string
"""

from __future__ import annotations

import json

import railtracks as rt

from src.db import queries


@rt.function_node
async def get_active_events() -> str:
    """Get all active global events for the current simulation session.
    Returns a JSON list of events with their prompts and timestamps."""
    session_id = rt.context.get("session_id")
    db = rt.context.get("db_session")
    events = await queries.get_events_for_session(db, session_id)
    return json.dumps(
        [{"prompt": e.event_prompt, "time": e.virtual_time.isoformat()} for e in events]
    )


@rt.function_node
async def get_recent_memories(limit: int = 10) -> str:
    """Get the most recent action memories for this archetype.
    Returns a JSON list of memories with time, action_type, duration, and thinking.

    Args:
        limit (int): Number of recent memories to retrieve (default 10).
    """
    session_id = rt.context.get("session_id")
    archetype_id = rt.context.get("archetype_id")
    db = rt.context.get("db_session")
    memories = await queries.get_recent_memories(db, session_id, archetype_id, limit)
    return json.dumps(
        [
            {
                "time": m.virtual_time.isoformat(),
                "action_type": m.action_type,
                "duration": m.duration,
                "thinking": m.thinking,
            }
            for m in memories
        ]
    )


@rt.function_node
async def get_follower_stats() -> str:
    """Get aggregate statistics about followers in this archetype.
    Returns JSON with count, avg_happiness, min_happiness, max_happiness."""
    session_id = rt.context.get("session_id")
    archetype_id = rt.context.get("archetype_id")
    db = rt.context.get("db_session")
    stats = await queries.get_follower_stats(db, session_id, archetype_id)
    return json.dumps(
        {k: float(v) if v is not None else None for k, v in stats.items()}
    )


@rt.function_node
async def get_nearby_locations(location_type: str = "all") -> str:
    """Get locations in this archetype's geographic region.
    Returns a JSON list of locations with name, type, and position.

    Args:
        location_type (str): Filter by type: 'neighborhood', 'district', 'building', 'landmark', or 'all'.
    """
    region = rt.context.get("region")
    db = rt.context.get("db_session")
    loc_type = None if location_type == "all" else location_type
    locations = await queries.get_locations_by_region(db, region, loc_type)
    return json.dumps(
        [{"name": loc.name, "type": loc.type, "position": loc.position} for loc in locations]
    )


@rt.function_node
async def get_relationships() -> str:
    """Get relationship summary for followers in this archetype.
    Returns JSON with relationship_count, avg_strength, min_strength, max_strength."""
    session_id = rt.context.get("session_id")
    archetype_id = rt.context.get("archetype_id")
    db = rt.context.get("db_session")
    summary = await queries.get_relationship_summary(db, session_id, archetype_id)
    return json.dumps(
        {k: float(v) if v is not None else None for k, v in summary.items()}
    )


@rt.function_node
async def get_current_time() -> str:
    """Get the current virtual time, when last actions finish, and the next tick time.
    Returns JSON with current_time, actions_finish_at, and next_tick_time as ISO strings."""
    return json.dumps(
        {
            "current_time": rt.context.get("virtual_time"),
            "actions_finish_at": rt.context.get("actions_finish_at"),
            "next_tick_time": rt.context.get("next_tick_time"),
        }
    )
