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

import logging
import random
import math
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.avatar.generator import generate_avatar_from_seed
from src.db.models import Location, Demographic, Session as SessionModel
from src.db.queries import (
    batch_insert_archetypes,
    batch_insert_followers,
    batch_insert_companies,
    batch_insert_relationships,
)
from src.data.toronto_neighborhoods import TORONTO_NEIGHBORHOODS
from shapely.geometry import Point
from src.data.toronto_zones import (
    ALL_ZONE_BOUNDS,
    ALL_CELLS,
    RESIDENTIAL_NEIGHBORHOODS,
    WORK_DISTRICTS,
    NEIGHBORHOOD_NAMES,
    _FALLBACK_POSITION,
)
from src.data.industry_mapping import (
    INDUSTRY_REGIONS,
    INDUSTRY_WORK_DISTRICTS,
    INDUSTRY_HOME_WEIGHTS,
    INDUSTRIES,
    INDUSTRY_DISTRIBUTION,
)
from src.data.demographics import (
    SOCIAL_CLASSES,
    SOCIAL_CLASS_WEIGHTS_BY_REGION,
    SOCIAL_CLASS_WEIGHTS_BY_NEIGHBORHOOD,
    DEFAULT_SOCIAL_CLASS_WEIGHTS,
    AGE_DISTRIBUTION,
    GENDER_DISTRIBUTION,
    RACE_DISTRIBUTION,
    FIRST_NAMES,
    LAST_NAMES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _random_position(zone_name: str) -> list[float]:
    """Return a random [lat, lng] within the Voronoi cell for *zone_name*.

    Uses rejection sampling: generates random points within the cell's
    bounding box and checks if they fall inside the polygon. Falls back
    to the cell centroid after 100 attempts, or to the Downtown Core
    center if the zone is not found.
    """
    cell = ALL_CELLS.get(zone_name)
    if cell is None:
        logger.warning(
            "Zone %r not found in ALL_CELLS; using fallback position", zone_name
        )
        return [
            _FALLBACK_POSITION[0] + random.uniform(-0.005, 0.005),
            _FALLBACK_POSITION[1] + random.uniform(-0.005, 0.005),
        ]
    b = cell.bounds  # (min_lng, min_lat, max_lng, max_lat)
    for _ in range(100):
        lng = random.uniform(b[0], b[2])
        lat = random.uniform(b[1], b[3])
        if cell.contains(Point(lng, lat)):
            return [round(lat, 6), round(lng, 6)]
    # Fallback: use centroid
    return [round(cell.centroid.y, 6), round(cell.centroid.x, 6)]


def _pick_home_neighborhood(industry: str) -> str:
    """Pick a residential neighborhood for workers in *industry* using
    INDUSTRY_HOME_WEIGHTS.  Falls back to uniform random if weights are
    not defined for the industry.
    """
    weights_map = INDUSTRY_HOME_WEIGHTS.get(industry)
    if not weights_map:
        logger.warning(
            "No home weights for industry %r; picking uniformly", industry
        )
        return random.choice(NEIGHBORHOOD_NAMES)

    neighborhoods = list(weights_map.keys())
    weights = list(weights_map.values())
    return random.choices(neighborhoods, weights=weights, k=1)[0]


def _pick_work_district(industry: str) -> str:
    """Pick a work district for *industry*.

    Uses new INDUSTRY_WORK_DISTRICTS first, falls back to INDUSTRY_REGIONS.
    """
    districts = INDUSTRY_WORK_DISTRICTS.get(industry)
    if districts:
        return random.choice(districts)

    # Fallback to legacy mapping
    regions = INDUSTRY_REGIONS.get(industry)
    if regions:
        logger.warning(
            "Industry %r not in INDUSTRY_WORK_DISTRICTS; using legacy INDUSTRY_REGIONS",
            industry,
        )
        return random.choice(regions)

    logger.warning("Industry %r has no work district mapping; defaulting", industry)
    return "Financial District"


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


def _random_social_class(neighborhood: str) -> str:
    """Pick social class based on the residential neighborhood.

    Tries the new SOCIAL_CLASS_WEIGHTS_BY_NEIGHBORHOOD first, then falls
    back to legacy SOCIAL_CLASS_WEIGHTS_BY_REGION, then DEFAULT weights.
    """
    weights = SOCIAL_CLASS_WEIGHTS_BY_NEIGHBORHOOD.get(neighborhood)
    if weights is None:
        weights = SOCIAL_CLASS_WEIGHTS_BY_REGION.get(
            neighborhood, DEFAULT_SOCIAL_CLASS_WEIGHTS
        )
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
    archetype_meta: list[dict] = []

    for industry, count in industry_archetype_counts.items():
        for _ in range(count):
            work_district = _pick_work_district(industry)
            home_neighborhood = _pick_home_neighborhood(industry)
            social_class = _random_social_class(home_neighborhood)

            # `region` is set to home_neighborhood for backward compat
            archetypes_data.append(
                {
                    "session_id": session_id,
                    "archetype_id": archetype_id,
                    "industry": industry,
                    "region": home_neighborhood,
                    "social_class": social_class,
                    "home_neighborhood": home_neighborhood,
                    "work_district": work_district,
                }
            )
            archetype_meta.append(
                {
                    "archetype_id": archetype_id,
                    "industry": industry,
                    "region": home_neighborhood,
                    "social_class": social_class,
                    "home_neighborhood": home_neighborhood,
                    "work_district": work_district,
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
    archetype_followers: dict[int, list[int]] = {
        m["archetype_id"]: [] for m in archetype_meta
    }

    for i, meta in enumerate(archetype_meta):
        count = followers_per_archetype + (1 if i < extra else 0)
        arch_id = meta["archetype_id"]
        home_neighborhood = meta["home_neighborhood"]
        work_district = meta["work_district"]

        for _ in range(count):
            home_pos = _random_position(home_neighborhood)
            work_pos = _random_position(work_district)
            # Deterministic avatar seed: same (session, follower) → same avatar
            avatar_seed = (hash((session_id, follower_id)) & 0x7FFFFFFF) or 1
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
                    "avatar_seed": avatar_seed,
                    "avatar_params": None,
                    "home_neighborhood": home_neighborhood,
                    "work_district": work_district,
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
        for idx in range(count):
            work_district = _pick_work_district(industry)
            companies_data.append(
                {
                    "session_id": session_id,
                    "company_id": company_id,
                    "name": _company_name(industry, idx),
                    "industry": industry,
                    "region": work_district,  # backward compat
                    "position": _random_position(work_district),
                    "work_district": work_district,
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
    if total_followers >= 2:
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
            region=meta["home_neighborhood"],
            home_neighborhood=meta["home_neighborhood"],
            work_district=meta["work_district"],
        )
        db.add(demo)

    for comp in companies_data:
        demo = Demographic(
            session_id=session_id,
            is_company=True,
            industry=comp["industry"],
            social_class=None,
            region=comp["work_district"],
            home_neighborhood=None,
            work_district=comp["work_district"],
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
