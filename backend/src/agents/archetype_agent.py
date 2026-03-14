"""
Tier 1 archetype agent — one LLM call per archetype per tick.

Uses gpt-5.4 with tools for autonomous context gathering. The agent decides
which tools to call (up to 10) and returns a validated ArchetypeResponse.
"""

from __future__ import annotations

import railtracks as rt

from src.agents.schemas import ArchetypeResponse
from src.agents.tools import (
    get_active_events,
    get_current_time,
    get_follower_stats,
    get_nearby_locations,
    get_recent_memories,
    get_relationships,
)

archetype_llm = rt.llm.OpenAILLM("gpt-4.1")


def build_archetype_agent(archetype):
    """Build a Railtracks agent node configured for a specific archetype.

    Parameters
    ----------
    archetype : Archetype
        SQLAlchemy model instance with industry, social_class, region attributes.

    Returns
    -------
    A Railtracks agent node class ready for use with ``rt.call()``.
    """
    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    work = getattr(archetype, "work_district", None) or archetype.region
    system_message = (
        f"You are simulating a demographic group in Toronto: "
        f"{archetype.industry} workers, {archetype.social_class or 'mixed'} class, "
        f"living in {home}, working in {work}.\n\n"
        "Use your tools to gather context before making decisions:\n"
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
