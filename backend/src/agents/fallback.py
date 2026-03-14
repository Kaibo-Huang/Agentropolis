"""
Deterministic fallback actions when all LLM retries fail.

Guarantees the simulation never halts by producing valid actions for any
time of day. Fallback actions follow a standard daily routine pattern.
"""

from __future__ import annotations

from datetime import datetime

from src.agents.schemas import ActionParams, ArchetypeAction, ArchetypeResponse


def generate_fallback_actions(virtual_time: datetime) -> ArchetypeResponse:
    """Generate deterministic fallback actions based on time of day.

    Called when all LLM retries are exhausted. Returns a valid
    ArchetypeResponse so the simulation tick can proceed.

    Parameters
    ----------
    virtual_time : datetime
        The current (or target) virtual time in the simulation.

    Returns
    -------
    ArchetypeResponse
        A response with reasonable default actions and no tweet.
    """
    hour = virtual_time.hour

    if 0 <= hour < 6:
        actions = [
            ArchetypeAction(
                action_type="sleep",
                action_params=ActionParams(),
                duration=6.0 - hour,
                thinking="Sleeping through the night (fallback).",
            )
        ]
    elif 6 <= hour < 7:
        actions = [
            ArchetypeAction(
                action_type="eat",
                action_params=ActionParams(),
                duration=0.5,
                thinking="Morning breakfast (fallback).",
            ),
            ArchetypeAction(
                action_type="commute",
                action_params=ActionParams(),
                duration=0.5,
                thinking="Commuting to work (fallback).",
            ),
        ]
    elif 7 <= hour < 12:
        actions = [
            ArchetypeAction(
                action_type="work",
                action_params=ActionParams(),
                duration=min(5, 12 - hour),
                thinking="Working morning shift (fallback).",
            )
        ]
    elif 12 <= hour < 13:
        actions = [
            ArchetypeAction(
                action_type="eat",
                action_params=ActionParams(),
                duration=1.0,
                thinking="Lunch break (fallback).",
            )
        ]
    elif 13 <= hour < 17:
        actions = [
            ArchetypeAction(
                action_type="work",
                action_params=ActionParams(),
                duration=min(4, 17 - hour),
                thinking="Working afternoon shift (fallback).",
            )
        ]
    elif 17 <= hour < 18:
        actions = [
            ArchetypeAction(
                action_type="commute",
                action_params=ActionParams(),
                duration=1.0,
                thinking="Commuting home (fallback).",
            )
        ]
    elif 18 <= hour < 19:
        actions = [
            ArchetypeAction(
                action_type="eat",
                action_params=ActionParams(),
                duration=1.0,
                thinking="Dinner at home (fallback).",
            )
        ]
    elif 19 <= hour < 22:
        actions = [
            ArchetypeAction(
                action_type="socialize",
                action_params=ActionParams(),
                duration=min(3, 22 - hour),
                thinking="Evening leisure time (fallback).",
            )
        ]
    else:  # 22-24
        actions = [
            ArchetypeAction(
                action_type="sleep",
                action_params=ActionParams(),
                duration=24 - hour + 6,
                thinking="Going to sleep for the night (fallback).",
            )
        ]

    return ArchetypeResponse(actions=actions, tweet=None)
