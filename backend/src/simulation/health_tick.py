"""
Daily health tick processor for disease transmission and incidence.

Called when a simulation tick crosses a day boundary. Processes both
contagious diseases (intra-archetype transmission) and non-contagious
diseases (background incidence rates).
"""

from __future__ import annotations

import logging
import random
import uuid

from src.data.disease_configs import DISEASE_CONFIGS
from src.db import queries
from src.db.engine import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def run_health_tick(session_id: uuid.UUID) -> dict:
    """Run daily health tick: disease transmission and seeding.

    Parameters
    ----------
    session_id : uuid.UUID
        The simulation session to process health updates for.

    Returns
    -------
    dict
        Summary with contagious_new_infections, noncontagious_new_cases,
        and total_health_changes counts.
    """
    async with AsyncSessionLocal() as db:
        # Load ALL followers once (avoids double-load across contagious + non-contagious)
        all_followers = await queries.get_all_followers_for_session(db, session_id)

        # Group followers by archetype for contagious processing
        from collections import defaultdict
        by_archetype: dict[int, list] = defaultdict(list)
        for f in all_followers:
            by_archetype[f.archetype_id].append(f)

        contagious_updates: list[dict] = []
        noncontagious_updates: list[dict] = []

        # ------------------------------------------------------------------
        # 1. Contagious diseases — intra-archetype transmission
        # ------------------------------------------------------------------
        for disease in DISEASE_CONFIGS:
            if not disease.get("is_contagious", False):
                continue

            rate = disease["transmission_rate_per_day"]
            disease_name = disease["name"]

            for _arch_id, followers in by_archetype.items():
                infected = [
                    f
                    for f in followers
                    if disease_name in (f.status_ailments or [])
                ]
                healthy = [
                    f
                    for f in followers
                    if disease_name not in (f.status_ailments or [])
                ]

                if not infected or not healthy:
                    continue

                # Precompute transmission probability once per archetype
                transmission_prob = 1 - (1 - rate) ** len(infected)

                for healthy_follower in healthy:
                    if random.random() < transmission_prob:
                        new_ailments = list(healthy_follower.status_ailments or [])
                        new_ailments.append(disease_name)
                        contagious_updates.append(
                            {
                                "session_id": session_id,
                                "follower_id": healthy_follower.follower_id,
                                "status_ailments": new_ailments,
                            }
                        )

        # ------------------------------------------------------------------
        # 2. Non-contagious diseases — background incidence
        # ------------------------------------------------------------------
        for disease in DISEASE_CONFIGS:
            if disease.get("is_contagious", False):
                continue

            incidence = disease.get("incidence_rate_per_day", 0)
            disease_name = disease["name"]

            if incidence <= 0:
                continue

            eligible = [
                f
                for f in all_followers
                if disease_name not in (f.status_ailments or [])
            ]
            expected_cases = int(len(eligible) * incidence)

            if expected_cases > 0 and eligible:
                new_cases = random.sample(
                    eligible, min(expected_cases, len(eligible))
                )
                for follower in new_cases:
                    new_ailments = list(follower.status_ailments or [])
                    new_ailments.append(disease_name)
                    noncontagious_updates.append(
                        {
                            "session_id": session_id,
                            "follower_id": follower.follower_id,
                            "status_ailments": new_ailments,
                        }
                    )

        # ------------------------------------------------------------------
        # 3. Apply all health updates
        # ------------------------------------------------------------------
        all_updates = contagious_updates + noncontagious_updates
        if all_updates:
            await queries.batch_update_followers(db, all_updates)

        await db.commit()

    return {
        "contagious_new_infections": len(contagious_updates),
        "noncontagious_new_cases": len(noncontagious_updates),
        "total_health_changes": len(contagious_updates) + len(noncontagious_updates),
    }
