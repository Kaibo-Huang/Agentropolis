"""
Hourly tick orchestrator for the Agentropolis simulation.

Processes all archetypes in parallel (bounded by semaphore), running:
1. Tier 1 archetype agent  -> archetype-level action decisions
2. Persist memories
3. Tier 2 follower variation agent -> per-follower personalization
4. Persist follower updates and posts

The simulation never halts: deterministic fallback actions are used when
all LLM retries are exhausted.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta

import railtracks as rt
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.archetype_agent import build_archetype_agent
from src.agents.fallback import generate_fallback_actions
from src.agents.follower_variation import (
    build_follower_variation_prompt,
    follower_variation_agent,
)
from src.agents.schemas import ArchetypeResponse
from src.db import queries
from src.db.engine import AsyncSessionLocal
from src.db.models import Archetype

logger = logging.getLogger(__name__)

# In-process cache for location data (static reference table, never changes per tick)
_location_cache: dict[tuple[str, str | None], list] = {}


async def _with_own_session(query_fn, *args, **kwargs):
    """Run one DB query in a dedicated AsyncSession — safe for asyncio.gather parallelism."""
    async with AsyncSessionLocal() as db:
        return await query_fn(db, *args, **kwargs)


async def _get_locations_cached(region: str, location_type: str | None = None) -> list:
    """Return cached location rows; populate from DB on first access per region."""
    key = (region, location_type)
    if key not in _location_cache:
        locs = await _with_own_session(queries.get_locations_by_region, region, location_type)
        _location_cache[key] = locs
    return _location_cache[key]


MAX_CONCURRENT_ARCHETYPES = 10
MAX_LLM_RETRIES = 3


class _IdAllocator:
    """Thread-safe (async) ID range allocator to prevent race conditions."""

    def __init__(self, next_memory_id: int, next_post_id: int):
        self._lock = asyncio.Lock()
        self._next_memory = next_memory_id
        self._next_post = next_post_id

    async def allocate_memory_ids(self, count: int) -> int:
        """Reserve `count` memory IDs and return the start of the range."""
        async with self._lock:
            start = self._next_memory
            self._next_memory += count
            return start

    async def allocate_post_ids(self, count: int) -> int:
        """Reserve `count` post IDs and return the start of the range."""
        async with self._lock:
            start = self._next_post
            self._next_post += count
            return start


async def run_hourly_tick(
    session_id: uuid.UUID,
    target_time: datetime,
    tick_number: int,
) -> dict:
    """Run one hourly tick for all archetypes in a session.

    Parameters
    ----------
    session_id : uuid.UUID
        The simulation session to advance.
    target_time : datetime
        The virtual time this tick targets (current_time + 1 hour).
    tick_number : int
        Monotonically increasing tick counter for logging.

    Returns
    -------
    dict
        Summary with tick_number, virtual_time, archetypes_processed,
        and archetypes_failed counts.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_ARCHETYPES)

    async with AsyncSessionLocal() as db:
        session_obj = await queries.get_session(db, session_id)
        if not session_obj:
            raise ValueError(f"Session {session_id} not found")

        archetypes = await queries.get_archetypes_for_session(db, session_id)
        current_time = session_obj.virtual_time

        # Pre-fetch max IDs once to avoid race conditions in parallel processing
        next_memory_id = await queries.get_max_id(
            db, queries.Memory, session_id, "memory_id"
        )
        next_post_id = await queries.get_max_id(
            db, queries.Post, session_id, "post_id"
        )

    id_alloc = _IdAllocator(next_memory_id, next_post_id)

    async def process_archetype(archetype: Archetype) -> dict:
        async with semaphore:
            return await _process_single_archetype(
                session_id=session_id,
                archetype=archetype,
                current_time=current_time,
                target_time=target_time,
                tick_number=tick_number,
                id_alloc=id_alloc,
            )

    results = await asyncio.gather(
        *[process_archetype(a) for a in archetypes],
        return_exceptions=True,
    )

    # Update session virtual_time after all archetypes are processed
    async with AsyncSessionLocal() as db:
        await queries.update_session_virtual_time(db, session_id, target_time)
        await db.commit()

    successes = sum(1 for r in results if isinstance(r, dict))
    failures = sum(1 for r in results if isinstance(r, Exception))

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Archetype processing failed with exception: {r}")

    return {
        "tick_number": tick_number,
        "virtual_time": target_time.isoformat(),
        "archetypes_processed": successes,
        "archetypes_failed": failures,
    }


async def _prefetch_archetype_context(
    session_id: uuid.UUID,
    archetype: Archetype,
    current_time: datetime,
    target_time: datetime,
    tick_events: list,
) -> tuple[dict, list]:
    """Pre-fetch context and followers in parallel, each query in its own session.

    Using asyncio.gather on a single AsyncSession is unsafe (asyncpg is
    single-channel; concurrent execute() calls cause _connection_for_bind
    state errors on exception). Each query gets its own AsyncSession so they
    run truly in parallel — read time drops from ~6 x RTT to ~1 x RTT.

    Locations come from an in-process cache (static reference data).
    """
    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    work = getattr(archetype, "work_district", None) or archetype.region
    next_tick_time = target_time + timedelta(hours=1)

    (
        memories,
        follower_stats,
        relationships,
        followers,
        work_locations,
        home_locations,
    ) = await asyncio.gather(
        _with_own_session(queries.get_recent_memories, session_id, archetype.archetype_id, 5),
        _with_own_session(queries.get_follower_stats, session_id, archetype.archetype_id),
        _with_own_session(queries.get_relationship_summary, session_id, archetype.archetype_id),
        _with_own_session(queries.get_followers_by_archetype, session_id, archetype.archetype_id),
        _get_locations_cached(work, None),
        _get_locations_cached(home, None),
    )

    return {
        "current_time": current_time.isoformat(),
        "actions_finish_at": current_time.isoformat(),
        "next_tick_time": next_tick_time.isoformat(),
        "events": [e.event_prompt for e in tick_events],
        "recent_memories": [
            {"action": m.action_type, "duration": m.duration, "thinking": m.thinking}
            for m in memories
        ],
        "follower_stats": {
            k: round(float(v), 2) if v is not None else None
            for k, v in follower_stats.items()
        },
        "work_locations": [loc.name for loc in work_locations[:5]],
        "home_locations": [loc.name for loc in home_locations[:5]],
        "relationships": {
            k: round(float(v), 2) if v is not None else None
            for k, v in relationships.items()
        },
    }, followers


async def _process_single_archetype(
    session_id: uuid.UUID,
    archetype: Archetype,
    current_time: datetime,
    target_time: datetime,
    tick_number: int,
    id_alloc: _IdAllocator,
) -> dict:
    """Process a single archetype: LLM decision + follower variations + persist.

    Runs within its own database session/transaction. On commit failure the
    entire archetype tick is lost, but the simulation continues.
    """
    arch_id = archetype.archetype_id
    tick_events: list = []  # populated by event system when available

    # ------------------------------------------------------------------
    # 1. Pre-fetch context + followers in parallel (each query own session)
    # ------------------------------------------------------------------
    t = time.perf_counter()
    try:
        prefetched_context, followers = await _prefetch_archetype_context(
            session_id, archetype, current_time, target_time, tick_events
        )
        read_elapsed = time.perf_counter() - t
        logger.debug(
            "arch %d | read %.2fs | %d followers",
            arch_id, read_elapsed, len(followers),
        )
    except Exception as e:
        read_elapsed = time.perf_counter() - t
        logger.warning(
            "arch %d | read FAILED %.2fs: %s — using empty context",
            arch_id, read_elapsed, e,
        )
        prefetched_context = {
            "current_time": current_time.isoformat(),
            "next_tick_time": (target_time + timedelta(hours=1)).isoformat(),
            "recent_memories": [],
            "follower_stats": {},
            "relationships": {},
            "events": [ev.event_prompt for ev in tick_events],
            "home_locations": [],
            "work_locations": [],
        }
        followers = []

    # ------------------------------------------------------------------
    # 2. Get archetype response from LLM (with retry + fallback)
    # ------------------------------------------------------------------
    archetype_response = await _get_archetype_decision(
        session_id=session_id,
        archetype=archetype,
        current_time=current_time,
        target_time=target_time,
        tick_number=tick_number,
        prefetched_context=prefetched_context,
    )

    # ------------------------------------------------------------------
    # 3. Persist memories, generate follower variations, and write updates
    # ------------------------------------------------------------------
    async with AsyncSessionLocal() as db:
        next_memory_id = await id_alloc.allocate_memory_ids(
            len(archetype_response.actions)
        )
        memories_data = []
        for i, action in enumerate(archetype_response.actions):
            memories_data.append(
                {
                    "session_id": session_id,
                    "memory_id": next_memory_id + i,
                    "archetype_id": arch_id,
                    "virtual_time": target_time,
                    "action_type": action.action_type,
                    "action_params": action.action_params.model_dump(),
                    "duration": action.duration,
                    "thinking": action.thinking,
                }
            )

        if followers:
            async def persist_memories():
                await queries.batch_insert_memories(db, memories_data)

            async def gen_variations():
                return await _generate_follower_variations(
                    db=db,
                    session_id=session_id,
                    archetype=archetype,
                    archetype_response=archetype_response,
                    followers=followers,
                    target_time=target_time,
                    id_alloc=id_alloc,
                )

            _, (follower_updates, new_posts) = await asyncio.gather(
                persist_memories(),
                gen_variations(),
            )

            if follower_updates:
                await queries.batch_update_followers(db, follower_updates)

            if new_posts:
                await queries.batch_insert_posts(db, new_posts)
        else:
            await queries.batch_insert_memories(db, memories_data)

        await db.commit()

    return {
        "archetype_id": arch_id,
        "actions": len(archetype_response.actions),
        "followers_updated": len(followers) if followers else 0,
    }


async def _get_archetype_decision(
    session_id: uuid.UUID,
    archetype: Archetype,
    current_time: datetime,
    target_time: datetime,
    tick_number: int,
    prefetched_context: dict | None = None,
) -> ArchetypeResponse:
    """Get archetype decision with retry and deterministic fallback.

    Retry strategy:
      1. Normal call
      2. Retry with error context appended
      3. Final retry with simplified prompt
      4. Deterministic fallback (simulation never halts)
    """
    agent = build_archetype_agent(archetype)

    for attempt in range(MAX_LLM_RETRIES):
        try:
            with rt.Session(
                name=f"tick-{session_id}-arch-{archetype.archetype_id}",
                context={
                    "session_id": session_id,
                    "archetype_id": archetype.archetype_id,
                    "region": archetype.region,
                    "home_neighborhood": getattr(archetype, "home_neighborhood", None) or archetype.region,
                    "work_district": getattr(archetype, "work_district", None) or archetype.region,
                    "virtual_time": current_time.isoformat(),
                    "prefetched_context": prefetched_context or {},
                },
                timeout=30.0,
                save_state=False,
            ):
                user_msg = f"Make decisions for tick {tick_number}."
                if attempt > 0:
                    user_msg += (
                        f" (Retry attempt {attempt + 1}. Previous attempt failed.)"
                    )

                result = await rt.call(agent, user_msg)
                return result.structured
        except Exception as e:
            logger.warning(
                "Archetype %d LLM attempt %d failed: %s (cause: %s)",
                archetype.archetype_id,
                attempt + 1,
                e,
                e.__cause__,
            )
            if attempt == MAX_LLM_RETRIES - 1:
                logger.error(
                    "Archetype %d all retries failed, using fallback",
                    archetype.archetype_id,
                )
                return generate_fallback_actions(target_time)

    # Unreachable in normal flow, but guarantees no halt
    return generate_fallback_actions(target_time)


async def _generate_follower_variations(
    db: AsyncSession,
    session_id: uuid.UUID,
    archetype: Archetype,
    archetype_response: ArchetypeResponse,
    followers: list,
    target_time: datetime,
    id_alloc: _IdAllocator,
) -> tuple[list[dict], list[dict]]:
    """Generate follower variations via gpt-4.1-mini.

    Returns
    -------
    tuple[list[dict], list[dict]]
        (follower_updates, post_dicts) — ready for batch_update_followers
        and batch_insert_posts respectively.
    """
    prompt = build_follower_variation_prompt(
        archetype, archetype_response, followers
    )

    try:
        with rt.Session(
            name=f"variation-{session_id}-arch-{archetype.archetype_id}",
            timeout=15.0,
            save_state=False,
        ):
            result = await rt.call(follower_variation_agent, prompt)
            batch = result.structured
    except Exception as e:
        logger.warning(
            "Follower variation failed for archetype %d: %s. Using defaults.",
            archetype.archetype_id,
            e,
        )
        # Fallback: no variations applied
        return [], []

    updates = []
    raw_posts = []
    follower_map = {f.follower_id: f for f in followers}

    for var in batch.variations:
        if var.follower_id not in follower_map:
            continue

        follower = follower_map[var.follower_id]

        # Calculate new happiness (clamped 0-1)
        new_happiness = max(0.0, min(1.0, follower.happiness + var.happiness_delta))

        update_dict: dict = {
            "session_id": session_id,
            "follower_id": var.follower_id,
            "happiness": new_happiness,
        }

        if var.position:
            update_dict["position"] = var.position

        updates.append(update_dict)

        # Collect post without ID (will allocate in bulk)
        if var.tweet_text:
            raw_posts.append(
                {
                    "session_id": session_id,
                    "follower_id": var.follower_id,
                    "text": var.tweet_text,
                    "virtual_time": target_time,
                }
            )

    # Bulk-allocate post IDs (race-safe)
    if raw_posts:
        post_start = await id_alloc.allocate_post_ids(len(raw_posts))
        for i, post in enumerate(raw_posts):
            post["post_id"] = post_start + i

    return updates, raw_posts
