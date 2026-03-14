"""
Agentropolis session seeder.

Generates all entities for a new simulation session in a single database
transaction.  If any step fails, the caller's transaction is rolled back.

Usage
-----
    async with AsyncSessionLocal() as db:
        async with db.begin():
            session_obj = await create_session(db, config=config)
            result = await seed_session(db, session_obj, config)
            # transaction commits on context-manager exit
"""

from __future__ import annotations

import random
import math
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Location, Demographic, Session as SessionModel
from src.db.queries import (
    batch_insert_archetypes,
    batch_insert_followers,
    batch_insert_companies,
    batch_insert_relationships,
)
from src.data.toronto_neighborhoods import TORONTO_NEIGHBORHOODS, NEIGHBORHOOD_BOUNDS
from src.data.industry_mapping import INDUSTRY_REGIONS, INDUSTRIES, INDUSTRY_DISTRIBUTION
from src.data.demographics import (
    SOCIAL_CLASSES,
    SOCIAL_CLASS_WEIGHTS_BY_REGION,
    DEFAULT_SOCIAL_CLASS_WEIGHTS,
    AGE_DISTRIBUTION,
    GENDER_DISTRIBUTION,
    RACE_DISTRIBUTION,
    FIRST_NAMES,
    LAST_NAMES,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _random_position(region: str) -> list[float]:
    """Return a random [lat, lng] within the bounding box for *region*."""
    bounds = NEIGHBORHOOD_BOUNDS.get(region)
    if bounds is None:
        # Fallback: Toronto city centre with small jitter
        return [
            43.6510 + random.uniform(-0.005, 0.005),
            -79.3832 + random.uniform(-0.005, 0.005),
        ]
    lat = random.uniform(bounds["min_lat"], bounds["max_lat"])
    lng = random.uniform(bounds["min_lng"], bounds["max_lng"])
    return [round(lat, 6), round(lng, 6)]


def _random_age() -> int:
    """Return a random age drawn from AGE_DISTRIBUTION."""
    buckets = [(lo, hi) for lo, hi, _ in AGE_DISTRIBUTION]
    weights = [w for _, _, w in AGE_DISTRIBUTION]
    lo, hi = random.choices(buckets, weights=weights, k=1)[0]
    return random.randint(lo, hi)


def _random_gender() -> str:
    genders = list(GENDER_DISTRIBUTION.keys())
    weights = list(GENDER_DISTRIBUTION.values())
    return random.choices(genders, weights=weights, k=1)[0]


def _random_race() -> str:
    races = list(RACE_DISTRIBUTION.keys())
    weights = list(RACE_DISTRIBUTION.values())
    return random.choices(races, weights=weights, k=1)[0]


def _random_social_class(region: str) -> str:
    weights = SOCIAL_CLASS_WEIGHTS_BY_REGION.get(region, DEFAULT_SOCIAL_CLASS_WEIGHTS)
    return random.choices(SOCIAL_CLASSES, weights=weights, k=1)[0]


def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _proportional_distribution(total: int, weights: dict[str, float]) -> dict[str, int]:
    """
    Distribute *total* items across keys using *weights* (need not sum to 1).
    Guarantees the returned counts sum to exactly *total* by giving remainders
    to the highest-fractional-part buckets.
    """
    total_weight = sum(weights.values())
    raw = {k: total * v / total_weight for k, v in weights.items()}
    floored = {k: int(v) for k, v in raw.items()}
    remainder = total - sum(floored.values())
    # Sort by descending fractional part to distribute leftovers fairly
    fractions = sorted(raw.keys(), key=lambda k: -(raw[k] - floored[k]))
    for i in range(remainder):
        floored[fractions[i]] += 1
    return floored


def _company_name(industry: str, index: int) -> str:
    """Generate a plausible company name for a given industry and index."""
    prefixes: dict[str, list[str]] = {
        "Finance": ["Capital", "Pinnacle", "Sterling", "Meridian", "Harbour"],
        "Tech": ["Nexus", "Pixel", "Orbit", "Apex", "Byte", "Synapse"],
        "Healthcare": ["CarePoint", "Vitality", "MedCore", "LifeWell", "PrimeCare"],
        "Retail": ["Metro", "Urban", "Maple", "Lakeview", "Crestview"],
        "Manufacturing": ["CanTech", "PrimeFab", "Ironside", "Precision", "Forge"],
        "Government": ["Public", "Civic", "Municipal", "Regional", "Crown"],
        "Education": ["Academy", "Scholars", "Meridian", "Horizon", "Collegiate"],
    }
    suffixes: dict[str, list[str]] = {
        "Finance": ["Group", "Partners", "Advisors", "Capital", "Wealth"],
        "Tech": ["Labs", "Systems", "Solutions", "Digital", "Works", "IO"],
        "Healthcare": ["Health", "Medical", "Clinic", "Wellness", "Sciences"],
        "Retail": ["Market", "Store", "Goods", "Retail", "Shop"],
        "Manufacturing": ["Industries", "Manufacturing", "Fabrication", "Works", "Corp"],
        "Government": ["Services", "Agency", "Department", "Office", "Bureau"],
        "Education": ["Institute", "College", "Academy", "School", "Centre"],
    }
    prefix_list = prefixes.get(industry, ["General"])
    suffix_list = suffixes.get(industry, ["Corp"])
    prefix = prefix_list[index % len(prefix_list)]
    suffix = suffix_list[(index // len(prefix_list)) % len(suffix_list)]
    return f"{prefix} {suffix}"


# ---------------------------------------------------------------------------
# Locations seeding (idempotent)
# ---------------------------------------------------------------------------


async def _seed_locations(db: AsyncSession) -> int:
    """
    Upsert TORONTO_NEIGHBORHOODS into the locations table.
    Skips entries whose (name, region) pair already exist.
    Returns the number of rows inserted.
    """
    # Fetch existing (name, region) pairs to avoid duplicates
    result = await db.execute(select(Location.name, Location.region))
    existing = {(row.name, row.region) for row in result}

    to_insert = [
        loc for loc in TORONTO_NEIGHBORHOODS
        if (loc["name"], loc["region"]) not in existing
    ]
    if not to_insert:
        return 0

    for loc_data in to_insert:
        loc = Location(
            name=loc_data["name"],
            type=loc_data["type"],
            region=loc_data["region"],
            position=loc_data["position"],
            metadata_=loc_data.get("metadata_"),
        )
        db.add(loc)

    await db.flush()
    return len(to_insert)


# ---------------------------------------------------------------------------
# Main seeder entry point
# ---------------------------------------------------------------------------


async def seed_session(
    db: AsyncSession,
    session_obj: SessionModel,
    config: dict,
) -> dict[str, Any]:
    """
    Generate all entities for a new simulation session.

    Parameters
    ----------
    db:
        An AsyncSession with an active transaction (begin() already called
        by the caller, or managed via the request lifecycle).
    session_obj:
        The already-persisted Session row (must have session_id set).
    config:
        Seeding parameters:
            total_population  (int, default 100)  — total follower count
            archetype_count   (int, default 10)   — number of archetypes
            company_count     (int, default 20)   — number of companies

    Returns
    -------
    dict with keys: locations_seeded, archetypes, followers, companies,
                    relationships, demographics
    """
    session_id = session_obj.session_id

    total_population: int = max(1, int(config.get("total_population", 100)))
    archetype_count: int = max(1, int(config.get("archetype_count", 10)))
    company_count: int = max(1, int(config.get("company_count", 20)))

    # Clamp archetype_count so we don't exceed population
    archetype_count = min(archetype_count, total_population)

    # ------------------------------------------------------------------
    # Step 1: Seed static locations (idempotent)
    # ------------------------------------------------------------------
    locations_seeded = await _seed_locations(db)

    # ------------------------------------------------------------------
    # Step 2: Generate archetypes
    # ------------------------------------------------------------------
    industry_archetype_counts = _proportional_distribution(
        archetype_count, INDUSTRY_DISTRIBUTION
    )

    archetypes_data: list[dict] = []
    archetype_id = 1

    # Track archetype metadata for downstream use
    archetype_meta: list[dict] = []  # {archetype_id, industry, region, social_class}

    for industry, count in industry_archetype_counts.items():
        regions_for_industry = INDUSTRY_REGIONS[industry]
        for _ in range(count):
            region = random.choice(regions_for_industry)
            social_class = _random_social_class(region)
            archetypes_data.append(
                {
                    "session_id": session_id,
                    "archetype_id": archetype_id,
                    "industry": industry,
                    "region": region,
                    "social_class": social_class,
                }
            )
            archetype_meta.append(
                {
                    "archetype_id": archetype_id,
                    "industry": industry,
                    "region": region,
                    "social_class": social_class,
                }
            )
            archetype_id += 1

    await batch_insert_archetypes(db, archetypes_data)

    # ------------------------------------------------------------------
    # Step 3: Generate followers
    # ------------------------------------------------------------------
    followers_per_archetype, extra = divmod(total_population, len(archetype_meta))

    followers_data: list[dict] = []
    follower_id = 1

    # Also track which archetype each follower belongs to (for relationships)
    # archetype_followers: archetype_id -> list[follower_id]
    archetype_followers: dict[int, list[int]] = {
        m["archetype_id"]: [] for m in archetype_meta
    }

    for i, meta in enumerate(archetype_meta):
        count = followers_per_archetype + (1 if i < extra else 0)
        arch_id = meta["archetype_id"]
        region = meta["region"]

        for _ in range(count):
            home_pos = _random_position(region)
            work_pos = _random_position(region)
            followers_data.append(
                {
                    "session_id": session_id,
                    "follower_id": follower_id,
                    "archetype_id": arch_id,
                    "name": _random_name(),
                    "age": _random_age(),
                    "gender": _random_gender(),
                    "race": _random_race(),
                    "home_position": home_pos,
                    "work_position": work_pos,
                    "position": home_pos,
                    "status_ailments": [],
                    "happiness": 0.5,
                    "volatility": round(random.uniform(0.1, 0.9), 4),
                }
            )
            archetype_followers[arch_id].append(follower_id)
            follower_id += 1

    await batch_insert_followers(db, followers_data)

    total_followers = len(followers_data)
    all_follower_ids = list(range(1, total_followers + 1))

    # ------------------------------------------------------------------
    # Step 4: Generate companies
    # ------------------------------------------------------------------
    industry_company_counts = _proportional_distribution(
        company_count, INDUSTRY_DISTRIBUTION
    )

    companies_data: list[dict] = []
    company_id = 1

    for industry, count in industry_company_counts.items():
        regions_for_industry = INDUSTRY_REGIONS[industry]
        for idx in range(count):
            region = random.choice(regions_for_industry)
            companies_data.append(
                {
                    "session_id": session_id,
                    "company_id": company_id,
                    "name": _company_name(industry, idx),
                    "industry": industry,
                    "region": region,
                    "position": _random_position(region),
                }
            )
            company_id += 1

    await batch_insert_companies(db, companies_data)

    # ------------------------------------------------------------------
    # Step 5: Generate relationships
    # ------------------------------------------------------------------
    relationships_data: list[dict] = []
    relation_id = 1

    def _add_rel(f1: int, f2: int, rel_type: str, strength: float | None = None) -> None:
        nonlocal relation_id
        if f1 == f2:
            return
        relationships_data.append(
            {
                "session_id": session_id,
                "relation_id": relation_id,
                "follower1_id": f1,
                "follower2_id": f2,
                "relation_type": rel_type,
                "relation_strength": round(
                    strength if strength is not None else random.uniform(0.3, 0.9), 4
                ),
            }
        )
        relation_id += 1

    # 5a. Coworker relationships: ~20% of intra-archetype pairs
    for arch_id, fids in archetype_followers.items():
        if len(fids) < 2:
            continue
        for i in range(len(fids)):
            for j in range(i + 1, len(fids)):
                if random.random() < 0.20:
                    _add_rel(fids[i], fids[j], "coworker")

    # 5b. Cross-archetype friendships: ~5% of random cross-archetype pairs
    #     Sample a manageable number of candidate pairs to avoid O(n^2) blowup
    #     on large populations.
    if total_followers >= 2:
        # Number of friendship candidates: scale with population but cap it
        num_friend_candidates = min(
            int(total_followers * (total_followers - 1) / 2 * 0.05),
            max(total_followers * 3, 100),
        )
        seen_pairs: set[tuple[int, int]] = set()
        attempts = 0
        max_attempts = num_friend_candidates * 5
        friendships_created = 0

        while friendships_created < num_friend_candidates and attempts < max_attempts:
            attempts += 1
            f1 = random.choice(all_follower_ids)
            f2 = random.choice(all_follower_ids)
            if f1 == f2:
                continue
            pair = (min(f1, f2), max(f1, f2))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            _add_rel(f1, f2, "friends")
            friendships_created += 1

    # 5c. Family relationships: ~3% of random pairs
    if total_followers >= 2:
        num_family = min(
            int(total_followers * (total_followers - 1) / 2 * 0.03),
            max(int(total_followers * 1.5), 50),
        )
        family_seen: set[tuple[int, int]] = set()
        family_attempts = 0
        max_family_attempts = num_family * 5
        family_created = 0

        while family_created < num_family and family_attempts < max_family_attempts:
            family_attempts += 1
            f1 = random.choice(all_follower_ids)
            f2 = random.choice(all_follower_ids)
            if f1 == f2:
                continue
            pair = (min(f1, f2), max(f1, f2))
            if pair in family_seen:
                continue
            family_seen.add(pair)
            _add_rel(f1, f2, "family", strength=random.uniform(0.6, 1.0))
            family_created += 1

    await batch_insert_relationships(db, relationships_data)

    # ------------------------------------------------------------------
    # Step 6: Insert demographic tracking records
    # ------------------------------------------------------------------
    for meta in archetype_meta:
        demo = Demographic(
            session_id=session_id,
            is_company=False,
            industry=meta["industry"],
            social_class=meta["social_class"],
            region=meta["region"],
        )
        db.add(demo)

    for comp in companies_data:
        demo = Demographic(
            session_id=session_id,
            is_company=True,
            industry=comp["industry"],
            social_class=None,
            region=comp["region"],
        )
        db.add(demo)

    await db.flush()

    # ------------------------------------------------------------------
    # Return summary counts
    # ------------------------------------------------------------------
    return {
        "locations_seeded": locations_seeded,
        "archetypes": len(archetypes_data),
        "followers": total_followers,
        "companies": len(companies_data),
        "relationships": len(relationships_data),
        "demographics": len(archetype_meta) + len(companies_data),
    }
