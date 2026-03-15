"""
ActiveEffects aggregator — merges all active events into a single effects snapshot
consumed by the tick pipeline.

Aggregation rules for concurrent events:
  - stay_home_rate:  max across events (most restrictive wins)
  - happiness_delta: sum, clamped to ±0.3
  - happiness_per_industry: sum per industry, clamped to ±0.3
  - tweet_rate_multiplier: product, capped at 5.0
  - tweet_sentiment: joined hints
  - disease_transmission_multiplier: product, capped at 10.0
  - gathering_zones: union, max pull_strength per zone
  - industry_stay_home: max per industry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ActiveEffects:
    """Aggregated effects from all active events for one tick."""

    stay_home_rate: float | None = None
    happiness_delta: float = 0.0
    happiness_per_industry: dict[str, float] = field(default_factory=dict)
    tweet_rate_multiplier: float = 1.0
    tweet_sentiment: str | None = None
    disease_transmission_multiplier: float = 1.0
    gathering_zones: list[dict] = field(default_factory=list)
    industry_stay_home: dict[str, float] = field(default_factory=dict)
    event_prompts: list[str] = field(default_factory=list)


def aggregate_active_effects(events: list, current_time: datetime) -> ActiveEffects:
    """Merge all active events into a single ActiveEffects snapshot.

    Parameters
    ----------
    events : list[Event]
        All events for the session (including expired ones for world history).
    current_time : datetime
        The session's current virtual time, used to filter expired effects.

    Returns
    -------
    ActiveEffects
        Aggregated effects. Neutral defaults when no events have effects.
    """
    result = ActiveEffects()
    sentiments: list[str] = []
    zone_map: dict[str, dict] = {}  # zone_name -> {pull_strength, start_hour, end_hour}

    for event in events:
        # Always collect prompts for LLM world history context
        result.event_prompts.append(event.event_prompt)

        # Skip events with no structured effects
        if event.effects is None:
            continue

        # Skip expired events (effects no longer apply, but prompt stays in history)
        if event.end_time is not None and event.end_time <= current_time:
            continue

        fx = event.effects

        # stay_home_rate: max (most restrictive)
        shr = fx.get("stay_home_rate")
        if shr is not None:
            result.stay_home_rate = max(result.stay_home_rate or 0.0, shr)

        # happiness_delta: sum
        hd = fx.get("happiness_delta")
        if hd is not None:
            result.happiness_delta += hd

        # happiness_per_industry: sum per industry (list of {industry, value})
        hpi = fx.get("happiness_per_industry")
        if hpi:
            for entry in hpi:
                ind = entry.get("industry", "")
                delta = entry.get("value", 0.0)
                result.happiness_per_industry[ind] = (
                    result.happiness_per_industry.get(ind, 0.0) + delta
                )

        # tweet_rate_multiplier: product
        trm = fx.get("tweet_rate_multiplier")
        if trm is not None:
            result.tweet_rate_multiplier *= trm

        # tweet_sentiment: collect all
        ts = fx.get("tweet_sentiment")
        if ts:
            sentiments.append(ts)

        # disease_transmission_multiplier: product
        dtm = fx.get("disease_transmission_multiplier")
        if dtm is not None:
            result.disease_transmission_multiplier *= dtm

        # gathering_zones: union, keep highest pull_strength per zone (with its hours)
        gz = fx.get("gathering_zones")
        if gz:
            for zone in gz:
                name = zone.get("zone_name", "")
                strength = zone.get("pull_strength", 0.0)
                existing = zone_map.get(name)
                if existing is None or strength > existing["pull_strength"]:
                    zone_map[name] = {
                        "pull_strength": strength,
                        "start_hour": zone.get("start_hour", 9),
                        "end_hour": zone.get("end_hour", 16),
                    }

        # industry_stay_home: max per industry (list of {industry, value})
        ish = fx.get("industry_stay_home")
        if ish:
            for entry in ish:
                ind = entry.get("industry", "")
                rate = entry.get("value", 0.0)
                result.industry_stay_home[ind] = max(
                    result.industry_stay_home.get(ind, 0.0), rate
                )

    # Apply caps
    result.happiness_delta = max(-0.3, min(0.3, result.happiness_delta))
    for ind in result.happiness_per_industry:
        result.happiness_per_industry[ind] = max(
            -0.3, min(0.3, result.happiness_per_industry[ind])
        )
    result.tweet_rate_multiplier = min(5.0, result.tweet_rate_multiplier)
    result.disease_transmission_multiplier = min(10.0, result.disease_transmission_multiplier)

    # Finalize sentiments and zones
    result.tweet_sentiment = ", ".join(sentiments) if sentiments else None
    result.gathering_zones = [
        {"zone_name": name, "pull_strength": z["pull_strength"],
         "start_hour": z["start_hour"], "end_hour": z["end_hour"]}
        for name, z in zone_map.items()
    ]

    return result
