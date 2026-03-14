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
    async with AsyncSessionLocal() as db:
        # ------------------------------------------------------------------
        # 1. Get archetype response from LLM (with retry + fallback)
        # ------------------------------------------------------------------
        archetype_response = await _get_archetype_decision(
            db=db,
            session_id=session_id,
            archetype=archetype,
            current_time=current_time,
            target_time=target_time,
            tick_number=tick_number,
        )

        # ------------------------------------------------------------------
        # 2. Persist memories (race-safe ID allocation)
        # ------------------------------------------------------------------
        next_memory_id = await id_alloc.allocate_memory_ids(
            len(archetype_response.actions)
        )
        memories_data = []
        for i, action in enumerate(archetype_response.actions):
            memories_data.append(
                {
                    "session_id": session_id,
                    "memory_id": next_memory_id + i,
                    "archetype_id": archetype.archetype_id,
                    "virtual_time": target_time,
                    "action_type": action.action_type,
                    "action_params": action.action_params,
                    "duration": action.duration,
                    "thinking": action.thinking,
                }
            )

        # ------------------------------------------------------------------
        # 3. Get followers and generate variations IN PARALLEL with memory persist
        # ------------------------------------------------------------------
        followers = await queries.get_followers_by_archetype(
            db, session_id, archetype.archetype_id
        )

        if followers:
            # Run memory persist and follower variation concurrently
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

            # 4. Apply follower updates
            if follower_updates:
                await queries.batch_update_followers(db, follower_updates)

            # 5. Batch-create posts
            if new_posts:
                await queries.batch_insert_posts(db, new_posts)
        else:
            await queries.batch_insert_memories(db, memories_data)

        await db.commit()

    return {
        "archetype_id": archetype.archetype_id,
        "actions": len(archetype_response.actions),
        "followers_updated": len(followers) if followers else 0,
    }


async def _get_archetype_decision(
    db: AsyncSession,
    session_id: uuid.UUID,
    archetype: Archetype,
    current_time: datetime,
    target_time: datetime,
    tick_number: int,
) -> ArchetypeResponse:
    """Get archetype decision with retry and deterministic fallback.

    Retry strategy:
      1. Normal call
      2. Retry with error context appended
      3. Final retry with simplified prompt
      4. Deterministic fallback (simulation never halts)
    """
    agent = build_archetype_agent(archetype)

    # Calculate time context
    actions_finish_at = current_time  # simplified: previous actions already finished
    next_tick_time = target_time + timedelta(hours=1)

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
                    "db_session": db,
                    "virtual_time": current_time.isoformat(),
                    "actions_finish_at": actions_finish_at.isoformat(),
                    "next_tick_time": next_tick_time.isoformat(),
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
                "Archetype %d LLM attempt %d failed: %s",
                archetype.archetype_id,
                attempt + 1,
                e,
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
