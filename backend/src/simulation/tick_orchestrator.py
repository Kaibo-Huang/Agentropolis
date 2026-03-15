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

from src.agents.archetype_agent import archetype_agent, build_archetype_user_message
from src.agents.fallback import generate_fallback_actions
from src.agents.follower_variation import build_tweet_prompt, tweet_agent
from src.agents.follower_rules import compute_happiness_delta, compute_position, select_tweeters
from src.agents.schemas import ArchetypeResponse
from src.db import queries
from src.db.engine import AsyncSessionLocal
from src.db.models import Archetype
from src.ws.manager import manager

logger = logging.getLogger(__name__)

MAX_CONCURRENT_ARCHETYPES = 100
MAX_LLM_RETRIES = 3

# In-process cache for location data (static reference table, never changes between ticks)
_location_cache: dict[tuple[str, str | None], list] = {}


async def _with_own_session(query_fn, *args, **kwargs):
    """Run one DB query in a dedicated AsyncSession — safe for asyncio.gather parallelism.

    asyncio.gather on a single AsyncSession is unsafe (asyncpg is single-channel;
    concurrent execute() calls race on _connection_for_bind and raise state errors).
    Each query in its own session runs truly in parallel at the cost of one connection
    per query — pool backpressure handles throttling naturally.
    """
    async with AsyncSessionLocal() as db:
        return await query_fn(db, *args, **kwargs)


async def _get_locations_cached(region: str, location_type: str | None = None) -> list:
    """Return cached location rows; hit DB only on first access per region."""
    key = (region, location_type)
    if key not in _location_cache:
        _location_cache[key] = await _with_own_session(
            queries.get_locations_by_region, region, location_type
        )
    return _location_cache[key]


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
    tick_start = time.perf_counter()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_ARCHETYPES)

    t0 = time.perf_counter()
    async with AsyncSessionLocal() as db:
        session_obj = await queries.get_session(db, session_id)
        if not session_obj:
            raise ValueError(f"Session {session_id} not found")

        archetypes = await queries.get_archetypes_for_session(db, session_id)
        current_time = session_obj.virtual_time

        # Fetch max IDs and shared tick events in parallel
        next_memory_id, next_post_id, tick_events = await asyncio.gather(
            queries.get_max_id(db, queries.Memory, session_id, "memory_id"),
            queries.get_max_id(db, queries.Post, session_id, "post_id"),
            queries.get_events_for_session(db, session_id),
        )
    logger.info(
        "TICK #%d | setup %.2fs | %d archetypes, %d events",
        tick_number,
        time.perf_counter() - t0,
        len(archetypes),
        len(tick_events),
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
                tick_events=tick_events,
            )

    await manager.broadcast(session_id, {
        "type": "tick_start",
        "data": {
            "tick_number": tick_number,
            "virtual_time": target_time.isoformat(),
            "archetype_count": len(archetypes),
        },
    })

    gather_start = time.perf_counter()
    results = await asyncio.gather(
        *[process_archetype(a) for a in archetypes],
        return_exceptions=True,
    )
    gather_elapsed = time.perf_counter() - gather_start

    # Update session virtual_time after all archetypes are processed
    async with AsyncSessionLocal() as db:
        await queries.update_session_virtual_time(db, session_id, target_time)
        await db.commit()

    successes = sum(1 for r in results if isinstance(r, dict))
    failures = sum(1 for r in results if isinstance(r, Exception))

    for r in results:
        if isinstance(r, Exception):
            logger.error("Archetype processing failed with exception: %s", r)

    await manager.broadcast(session_id, {
        "type": "tick_complete",
        "data": {
            "tick_number": tick_number,
            "virtual_time": target_time.isoformat(),
            "archetypes_processed": successes,
            "archetypes_failed": failures,
        },
    })

    total_elapsed = time.perf_counter() - tick_start
    logger.info(
        "TICK #%d | DONE %.2fs total (gather %.2fs) | ok=%d fail=%d",
        tick_number,
        total_elapsed,
        gather_elapsed,
        successes,
        failures,
    )

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
    """Fetch context + followers for one archetype, all queries truly in parallel.

    Each of the 6 queries runs in its own AsyncSession so asyncio.gather can
    overlap them. On a 120ms-RTT connection this drops phase-1 time from
    ~6 × 120ms = 720ms to ~1 × 120ms = 120ms.

    Location rows are served from an in-process cache after the first tick.

    Returns (context_dict, followers).
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
    tick_events: list,
) -> dict:
    """Process a single archetype: LLM decision + follower variations + persist.

    Three-phase structure:
      Phase 1 — short read-only DB session (pre-fetch context + followers).
      Phase 2 — LLM calls with no DB connection held.
      Phase 3 — short write DB session (memories + follower updates + posts).
    """
    arch_id = archetype.archetype_id
    arch_start = time.perf_counter()
    read_elapsed = llm1_elapsed = llm2_elapsed = write_elapsed = 0.0

    # ------------------------------------------------------------------
    # Phase 1: Read — brief DB session, released before any LLM call
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
            "events": [e.event_prompt for e in tick_events],
            "home_locations": [],
            "work_locations": [],
        }
        followers = []

    # ------------------------------------------------------------------
    # Phase 2: LLM calls — no DB connection held during network I/O
    # ------------------------------------------------------------------
    t = time.perf_counter()
    archetype_response = await _get_archetype_decision(
        session_id=session_id,
        archetype=archetype,
        tick_number=tick_number,
        target_time=target_time,
        prefetched_context=prefetched_context,
    )
    llm1_elapsed = time.perf_counter() - t

    # Broadcast the decision immediately — frontend gets archetype actions
    # ~3s before followers update, enabling early UI feedback.
    await manager.broadcast(session_id, {
        "type": "tick_archetype_decision",
        "data": {
            "archetype_id": archetype.archetype_id,
            "actions": [
                {
                    "action_type": a.action_type,
                    "location": a.action_params.location,
                    "duration": a.duration,
                }
                for a in archetype_response.actions
            ],
        },
    })

    follower_updates: list[dict] = []
    new_posts: list[dict] = []
    t = time.perf_counter()
    if followers:
        follower_updates, new_posts = await _generate_follower_variations(
            session_id=session_id,
            archetype=archetype,
            archetype_response=archetype_response,
            followers=followers,
            target_time=target_time,
            id_alloc=id_alloc,
        )
    llm2_elapsed = time.perf_counter() - t

    # ------------------------------------------------------------------
    # Phase 3: Write — new DB session, all writes in one transaction.
    # Broadcast runs concurrently with the write so the UI updates the
    # moment follower variation completes, not after the DB round-trip.
    # ------------------------------------------------------------------
    t = time.perf_counter()
    next_memory_id = await id_alloc.allocate_memory_ids(
        len(archetype_response.actions)
    )
    memories_data = [
        {
            "session_id": session_id,
            "memory_id": next_memory_id + i,
            "archetype_id": archetype.archetype_id,
            "virtual_time": target_time,
            "action_type": action.action_type,
            "action_params": action.action_params.model_dump(),
            "duration": action.duration,
            "thinking": action.thinking,
        }
        for i, action in enumerate(archetype_response.actions)
    ]

    ws_msg = {
        "type": "tick_archetype_update",
        "data": {
            "archetype_id": archetype.archetype_id,
            "followers": [
                {k: v for k, v in f.items() if k != "session_id"}
                for f in follower_updates
            ],
            "posts": [
                {
                    "post_id": p["post_id"],
                    "follower_id": p["follower_id"],
                    "text": p["text"],
                    "virtual_time": p["virtual_time"].isoformat(),
                }
                for p in new_posts
            ],
        },
    }

    async def _do_write() -> None:
        async with AsyncSessionLocal() as db:
            await queries.batch_insert_memories(db, memories_data)
            if follower_updates:
                await queries.batch_update_followers(db, follower_updates)
            if new_posts:
                await queries.batch_insert_posts(db, new_posts)
            await db.commit()

    await asyncio.gather(manager.broadcast(session_id, ws_msg), _do_write())
    write_elapsed = time.perf_counter() - t

    total_elapsed = time.perf_counter() - arch_start
    logger.info(
        "arch %d | %.2fs total  read=%.2fs  llm=%.2fs  var=%.2fs  write=%.2fs",
        arch_id, total_elapsed, read_elapsed, llm1_elapsed, llm2_elapsed, write_elapsed,
    )

    return {
        "archetype_id": arch_id,
        "actions": len(archetype_response.actions),
        "followers_updated": len(followers),
    }


async def _get_archetype_decision(
    session_id: uuid.UUID,
    archetype: Archetype,
    tick_number: int,
    target_time: datetime,
    prefetched_context: dict,
) -> ArchetypeResponse:
    """Get archetype decision — single LLM call with all context in the user message.

    Retry strategy:
      1-3. Retry with attempt number appended to message
      4.   Deterministic fallback (simulation never halts)
    """
    # Build the base prompt once — avoids 6x json.dumps() on every retry
    base_msg = build_archetype_user_message(
        archetype, tick_number, prefetched_context, attempt=0
    )

    for attempt in range(MAX_LLM_RETRIES):
        t = time.perf_counter()
        try:
            user_msg = (
                base_msg
                if attempt == 0
                else base_msg + f"\n(Retry attempt {attempt + 1}.)"
            )
            with rt.Session(
                name=f"tick-{session_id}-arch-{archetype.archetype_id}",
                timeout=15.0,
                save_state=False,
            ):
                result = await rt.call(archetype_agent, user_msg)
                logger.debug(
                    "arch %d | llm attempt %d ok %.2fs",
                    archetype.archetype_id, attempt + 1, time.perf_counter() - t,
                )
                return result.structured
        except Exception as e:
            logger.warning(
                "arch %d | llm attempt %d FAILED %.2fs: %s (cause: %s)",
                archetype.archetype_id,
                attempt + 1,
                time.perf_counter() - t,
                e,
                e.__cause__,
            )
            if attempt == MAX_LLM_RETRIES - 1:
                logger.error(
                    "arch %d | all %d retries failed, using fallback",
                    archetype.archetype_id, MAX_LLM_RETRIES,
                )
                return generate_fallback_actions(target_time)

    return generate_fallback_actions(target_time)


async def _generate_follower_variations(
    session_id: uuid.UUID,
    archetype: Archetype,
    archetype_response: ArchetypeResponse,
    followers: list,
    target_time: datetime,
    id_alloc: _IdAllocator,
) -> tuple[list[dict], list[dict]]:
    """Compute follower updates with rules; call LLM only for tweet text."""

    # ── Rule-based happiness + position for all followers ──
    updates = []
    for follower in followers:
        delta = compute_happiness_delta(archetype_response.actions, follower.volatility)
        new_happiness = max(0.0, min(1.0, follower.happiness + delta))
        update: dict = {
            "session_id": session_id,
            "follower_id": follower.follower_id,
            "happiness": new_happiness,
        }
        pos = compute_position(archetype_response.actions, follower)
        if pos:
            update["position"] = pos
        updates.append(update)

    # ── LLM tweet generation for ~10% of followers ──
    tweeters = select_tweeters(followers)
    raw_posts: list[dict] = []

    if tweeters:
        try:
            with rt.Session(
                name=f"tweets-{session_id}-arch-{archetype.archetype_id}",
                timeout=15.0,
                save_state=False,
            ):
                prompt = build_tweet_prompt(archetype, archetype_response, tweeters)
                result = await rt.call(tweet_agent, prompt)
                batch = result.structured

            tweeter_map = {f.follower_id: f for f in tweeters}
            for t in batch.tweets:
                if t.follower_id in tweeter_map and t.tweet_text:
                    raw_posts.append({
                        "session_id": session_id,
                        "follower_id": t.follower_id,
                        "text": t.tweet_text,
                        "virtual_time": target_time,
                    })
        except Exception as e:
            logger.warning(
                "Tweet generation failed for archetype %d: %s",
                archetype.archetype_id, e,
            )

    if raw_posts:
        post_start = await id_alloc.allocate_post_ids(len(raw_posts))
        for i, post in enumerate(raw_posts):
            post["post_id"] = post_start + i

    return updates, raw_posts
