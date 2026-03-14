"""
Tier 1 archetype agent — one LLM call per archetype per tick.

Context is pre-fetched in parallel before the LLM call and injected directly
into the prompt, eliminating tool-call round trips entirely.
"""

from __future__ import annotations

import json

import railtracks as rt

from src.agents.schemas import ArchetypeResponse

archetype_llm = rt.llm.OpenAILLM("gpt-4.1")


def build_archetype_agent(archetype, prefetched_context: dict | None = None):
    """Build a Railtracks agent node configured for a specific archetype.

    Parameters
    ----------
    archetype : Archetype
        SQLAlchemy model instance with industry, social_class, region attributes.
    prefetched_context : dict, optional
        Pre-fetched context data (events, memories, stats, locations, relationships).
        When provided, no tool calls are made — the agent answers in a single LLM pass.

    Returns
    -------
    A Railtracks agent node class ready for use with ``rt.call()``.
    """
    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    work = getattr(archetype, "work_district", None) or archetype.region

    base = (
        f"You are simulating a demographic group in Toronto: "
        f"{archetype.industry} workers, {archetype.social_class or 'mixed'} class, "
        f"living in {home}, working in {work}.\n\n"
    )

    if prefetched_context:
        context_block = json.dumps(prefetched_context, indent=2)
        system_message = (
            base
            + f"All context has been pre-loaded for you:\n{context_block}\n\n"
            "Generate actions directly using the context above. "
            "Each action needs: action_type, action_params, duration (hours), "
            "thinking (1 sentence max).\n"
            "Valid types: work, commute, eat, sleep, shop, exercise, socialize, "
            "post, attend_event, visit_family.\n"
            "Actions must fill the time gap between actions_finish_at and next_tick_time."
        )
        return rt.agent_node(
            name=f"archetype-{archetype.archetype_id}",
            llm=archetype_llm,
            system_message=system_message,
            tool_nodes=[],
            output_schema=ArchetypeResponse,
            max_tool_calls=0,
        )

    # Fallback: tool-based agent (used if pre-fetch fails)
    from src.agents.tools import (
        get_active_events,
        get_current_time,
        get_follower_stats,
        get_nearby_locations,
        get_recent_memories,
        get_relationships,
    )

    system_message = (
        base
        + "Use your tools to gather context before making decisions:\n"
        "- Check current time and how much time you need to fill\n"
        "- Look at recent memories to maintain continuity\n"
        "- Check active events that might affect behavior\n"
        "- Review follower stats (happiness, health) to inform decisions\n"
        "- Check nearby locations (zone='work' for work, zone='home' for home)\n"
        "- Review relationships for social action decisions\n\n"
        "Then generate actions. Each action needs: action_type, action_params, "
        "duration (hours), thinking (1 sentence max).\n"
        "Valid types: work, commute, eat, sleep, shop, exercise, socialize, "
        "post, attend_event, visit_family.\n"
        "Actions must fill the time gap between when current actions finish "
        "and the next tick."
    )
    return rt.agent_node(
        name=f"archetype-{archetype.archetype_id}",
        llm=archetype_llm,
        system_message=system_message,
        tool_nodes=[
            get_active_events,
            get_recent_memories,
            get_follower_stats,
            get_nearby_locations,
            get_relationships,
            get_current_time,
        ],
        output_schema=ArchetypeResponse,
        max_tool_calls=10,
    )
