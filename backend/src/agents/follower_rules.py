"""Rule-based happiness and position computation for follower variation."""

import random

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


def compute_position(actions: list, follower) -> list[float] | None:
    """
    Return new [lat, lng] position based on dominant action.
    Returns None if the follower shouldn't visibly move.
    """
    primary = dominant_action(actions)
    if primary is None:
        return None
    target = ACTION_POSITION_TARGET.get(primary)
    if target == "work":
        pos = getattr(follower, "work_position", None)
    elif target == "home":
        pos = getattr(follower, "home_position", None)
    else:
        return None  # "post" — stay put

    if not pos:
        return None
    # Normalise: accept both [lat, lng] list and {"lat":…,"lng":…} dict
    if isinstance(pos, list):
        return pos
    if isinstance(pos, dict):
        lat = pos.get("lat") or pos.get(0)
        lng = pos.get("lng") or pos.get(1)
        if lat is not None and lng is not None:
            return [float(lat), float(lng)]
    return None


def select_tweeters(followers: list, rate: float = 0.10) -> list:
    """Randomly select ~rate fraction of followers to tweet (min 0, no guaranteed minimum)."""
    return [f for f in followers if random.random() < rate]
