"""Rule-based happiness and position computation for follower variation."""

from __future__ import annotations

import math
import random

from shapely.geometry import Point
from src.data.toronto_zones import ALL_CELLS, ZONE_SEEDS

# Base happiness delta per action_type (before volatility scaling)
ACTION_HAPPINESS: dict[str, float] = {
    "work":         0.04,
    "commute":     -0.04,
    "eat":          0.06,
    "sleep":        0.08,
    "shop":         0.05,
    "exercise":     0.07,
    "socialize":    0.06,
    "post":         0.03,
    "attend_event": 0.08,
    "visit_family": 0.06,
}

# Which position the follower should be at for each action_type
ACTION_POSITION_TARGET = {
    "work":         "work",
    "commute":      "work",
    "sleep":        "home",
    "eat":          "home",
    "shop":         "home",   # near home neighborhood
    "exercise":     "home",
    "socialize":    "home",
    "post":         None,     # stay put
    "attend_event": "work",   # events happen downtown
    "visit_family": "home",
}


def dominant_action(actions: list) -> str | None:
    """Return the action_type with the longest duration; None if empty."""
    if not actions:
        return None
    return max(actions, key=lambda a: a.duration).action_type


def compute_happiness_delta(actions: list, volatility: float) -> float:
    """Sum base deltas across all actions, scale by volatility, clamp to ±0.2."""
    if not actions:
        return 0.0
    total_duration = sum(a.duration for a in actions) or 1.0
    weighted = sum(
        ACTION_HAPPINESS.get(a.action_type, 0.0) * (a.duration / total_duration)
        for a in actions
    )
    return max(-0.2, min(0.2, weighted * volatility))


MAX_JITTER = 0.009  # ~1 km in degrees


def _normalize_pos(pos) -> list[float] | None:
    """Accept [lat, lng] list or {"lat":…,"lng":…} dict; return [lat, lng] or None."""
    if isinstance(pos, list):
        return [float(pos[0]), float(pos[1])]
    if isinstance(pos, dict):
        lat = pos.get("lat") or pos.get(0)
        lng = pos.get("lng") or pos.get(1)
        if lat is not None and lng is not None:
            return [float(lat), float(lng)]
    return None


JITTER_CHANCE = 0.20  # only 20% of people move each tick


def _add_jitter(pos: list[float], zone_name: str | None = None) -> list[float] | None:
    """Add random movement with exponential falloff, clamped to zone boundary.

    80% of people don't move at all (returns None).
    Of the 20% that do move, most shift a little and a few up to ~1 km.
    Uses rejection sampling to stay within the zone.
    """
    if random.random() > JITTER_CHANCE:
        return None  # this follower stays put this tick

    cell = ALL_CELLS.get(zone_name) if zone_name else None

    for _ in range(5):
        theta = random.uniform(0, 2 * math.pi)
        r = min(random.expovariate(1 / 0.001), MAX_JITTER)
        candidate = [pos[0] + r * math.cos(theta), pos[1] + r * math.sin(theta)]
        if cell is None or cell.contains(Point(candidate[1], candidate[0])):
            return candidate
    return None


GATHERING_SCATTER = 0.004  # ~450m radius — fills a zone visually


def _scatter_around(pos: list[float], zone_name: str) -> list[float]:
    """Scatter a follower around a gathering zone center.

    Unlike _add_jitter, this ALWAYS returns a position (no 80% skip)
    and uses a wider radius so gathered crowds look like actual crowds
    on the map instead of a single stacked dot.
    """
    cell = ALL_CELLS.get(zone_name)

    for _ in range(8):
        theta = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, GATHERING_SCATTER)
        candidate = [pos[0] + r * math.cos(theta), pos[1] + r * math.sin(theta)]
        if cell is None or cell.contains(Point(candidate[1], candidate[0])):
            return candidate
    return pos  # fallback to center if all attempts rejected


WORK_START = 9   # 9 AM  (used by seeder for initial spawn)
WORK_END = 17    # 5 PM


def _follower_work_window(follower_id: int) -> tuple[int, int]:
    """Return (start_hour, end_hour) for this follower's personal work schedule.

    Deterministic per follower: start 7–11 AM, end 4–8 PM.
    """
    # Use different bits of follower_id for start vs end to avoid correlation
    start = 7 + (follower_id % 5)        # 7, 8, 9, 10, 11
    end = 16 + ((follower_id // 5) % 5)  # 16, 17, 18, 19, 20
    return start, end


def _zone_center(zone_name: str) -> list[float] | None:
    """Get the [lat, lng] center of a zone from its seed point.

    ZONE_SEEDS stores (lng, lat) tuples; we return [lat, lng].
    """
    seed = ZONE_SEEDS.get(zone_name)
    if seed is None:
        return None
    return [seed[1], seed[0]]  # (lng, lat) → [lat, lng]


def compute_position(
    actions: list,
    follower,
    hour: int = 12,
    active_effects=None,
    industry: str | None = None,
) -> list[float] | None:
    """
    Return new [lat, lng] position based on follower role, time of day,
    dominant action, and active event effects.

    Event effect overrides (checked in priority order before normal logic):
    1. Industry stay-home: per-industry fraction forced home
    2. Global stay-home: override the default 15% homebodies rate
    3. Gathering magnet: pull fraction of followers to a specific zone

    Normal logic (unchanged):
    15% of followers are homebodies (always at home),
    15% are workaholics (always at work),
    70% follow time-aware logic with per-follower work schedules.
    All positions include small random jitter so every dot moves each tick.
    """
    fid = follower.follower_id

    # ------------------------------------------------------------------
    # Event effect overrides (deterministic via follower_id)
    # ------------------------------------------------------------------
    if active_effects is not None:
        # Use a stable hash bucket (0-99) for deterministic per-follower decisions
        bucket = fid % 100

        # 1. Industry-specific stay-home override
        #    When an industry has an explicit rate, it REPLACES the global rate
        #    for that industry (e.g. Healthcare: 0.05 means only 5% stay home,
        #    even if global stay_home_rate is 0.80).
        _industry_has_override = (
            industry
            and active_effects.industry_stay_home
            and industry in active_effects.industry_stay_home
        )
        if _industry_has_override:
            ind_rate = active_effects.industry_stay_home[industry]
            if bucket < int(ind_rate * 100):
                # This fraction stays home
                pos = _normalize_pos(getattr(follower, "home_position", None))
                zone = getattr(follower, "home_neighborhood", None)
                if pos:
                    return _add_jitter(pos, zone) or pos
                return None
            # Essential worker — stays at work regardless of time of day.
            # (e.g. Healthcare: 0.05 means 95% keep working, even overnight)
            pos = _normalize_pos(getattr(follower, "work_position", None))
            zone = getattr(follower, "work_district", None)
            if pos:
                return _add_jitter(pos, zone) or pos
            return None

        # 2. Global stay-home override (only for industries WITHOUT a specific override)
        elif active_effects.stay_home_rate is not None:
            if bucket < int(active_effects.stay_home_rate * 100):
                pos = _normalize_pos(getattr(follower, "home_position", None))
                zone = getattr(follower, "home_neighborhood", None)
                if pos:
                    return _add_jitter(pos, zone) or pos
                return None

        # 3. Gathering zone magnet
        if active_effects.gathering_zones:
            for gz in active_effects.gathering_zones:
                # Skip zones outside their active time window
                s = gz.get("start_hour")
                e = gz.get("end_hour")
                if s is not None and e is not None and s != e:
                    if s < e:
                        if not (s <= hour < e):
                            continue
                    else:  # wraps midnight, e.g. 20–2
                        if not (hour >= s or hour < e):
                            continue
                # s == e or missing → always active

                zone_name = gz.get("zone_name", "")
                pull = gz.get("pull_strength", 0.0)
                # Deterministic hash (sum of ordinals, not Python hash() which is randomized)
                zone_hash = sum(ord(c) for c in zone_name) * 37
                pull_bucket = ((fid * 31) + zone_hash) % 100
                if pull_bucket < int(pull * 100):
                    center = _zone_center(zone_name)
                    if center:
                        return _scatter_around(center, zone_name)
                    continue  # zone not found, try next zone

    # ------------------------------------------------------------------
    # Normal position logic (unchanged)
    # ------------------------------------------------------------------
    role_bucket = fid % 20
    work_start, work_end = _follower_work_window(fid)
    is_work_hours = work_start <= hour < work_end

    if role_bucket <= 2:  # 15% homebodies — always at home
        pos = _normalize_pos(getattr(follower, "home_position", None))
        zone = getattr(follower, "home_neighborhood", None)
    elif role_bucket <= 5:  # 15% workaholics — always at work
        pos = _normalize_pos(getattr(follower, "work_position", None))
        zone = getattr(follower, "work_district", None)
    else:  # 70% normal — time-aware
        if is_work_hours:
            primary = dominant_action(actions)
            if primary is None:
                pos = _normalize_pos(getattr(follower, "position", None))
                zone = getattr(follower, "home_neighborhood", None)
            else:
                target = ACTION_POSITION_TARGET.get(primary)
                if target == "work":
                    pos = _normalize_pos(getattr(follower, "work_position", None))
                    zone = getattr(follower, "work_district", None)
                elif target == "home":
                    pos = _normalize_pos(getattr(follower, "home_position", None))
                    zone = getattr(follower, "home_neighborhood", None)
                else:
                    pos = _normalize_pos(getattr(follower, "position", None))
                    zone = getattr(follower, "home_neighborhood", None)
        else:
            pos = _normalize_pos(getattr(follower, "home_position", None))
            zone = getattr(follower, "home_neighborhood", None)

    if not pos:
        return None

    return _add_jitter(pos, zone)


def select_tweeters(followers: list, rate: float = 0.10) -> list:
    """Randomly select ~rate fraction of followers to tweet (min 0, no guaranteed minimum)."""
    return [f for f in followers if random.random() < rate]
