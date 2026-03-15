"""
Tier 1 archetype agent — one LLM call per archetype per tick.

Context is pre-fetched in parallel before the LLM call and injected directly
into the user message, eliminating tool-call round trips entirely.
"""

from __future__ import annotations

import json

import railtracks as rt

from src.agents.schemas import ArchetypeResponse

archetype_llm = rt.llm.OpenAILLM("gpt-4.1-mini")

# Single shared agent node — context is passed per-call in the user message.
archetype_agent = rt.agent_node(
    name="archetype-decision",
    llm=archetype_llm,
    system_message=(
        "You are simulating a demographic group in Toronto. "
        "All context you need is provided in the user message. "
        "Generate actions that fill the time gap between current_time and target_time. "
        "Each action requires: action_type, action_params (dict), duration (hours), "
        "thinking (1 sentence max).\n"
        "Valid action_types: work, commute, eat, sleep, shop, exercise, socialize, "
        "post, attend_event, visit_family."
    ),
    output_schema=ArchetypeResponse,
)


def build_archetype_user_message(
    archetype,
    tick_number: int,
    prefetched_context: dict,
    attempt: int = 0,
) -> str:
    """Build the user message with all pre-fetched context inline."""
    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    work = getattr(archetype, "work_district", None) or archetype.region

    ctx = prefetched_context
    memories_str = json.dumps(ctx.get("recent_memories", []))
    follower_str = json.dumps(ctx.get("follower_stats", {}))
    rel_str = json.dumps(ctx.get("relationships", {}))
    events_str = json.dumps(ctx.get("events", []))
    effects_str = json.dumps(ctx.get("event_effects_summary", {}))
    home_locs = json.dumps(ctx.get("home_locations", []))
    work_locs = json.dumps(ctx.get("work_locations", []))

    retry_note = f"\n(Retry attempt {attempt + 1}.)" if attempt > 0 else ""

    return (
        f"Archetype: {archetype.industry} workers, {archetype.social_class or 'mixed'} class, "
        f"living in {home}, working in {work}.\n\n"
        f"TICK #{tick_number}\n"
        f"Current time: {ctx['current_time']}\n"
        f"Target time (fill actions up to): {ctx['next_tick_time']}\n\n"
        f"Recent memories:\n{memories_str}\n\n"
        f"Follower stats: {follower_str}\n\n"
        f"Relationship summary: {rel_str}\n\n"
        f"Active events: {events_str}\n\n"
        f"City conditions: {effects_str}\n\n"
        f"Home neighborhood locations ({home}): {home_locs}\n\n"
        f"Work district locations ({work}): {work_locs}\n\n"
        f"Generate actions to fill the time from {ctx['current_time']} to {ctx['next_tick_time']}."
        f"{retry_note}"
    )
