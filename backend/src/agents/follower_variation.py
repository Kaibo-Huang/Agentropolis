"""
Tier 2 follower variation agent — prompt-only, no tools.

Uses gpt-4.1-mini to generate per-follower variations from the archetype's
action plan. All context is pre-loaded into the prompt (no tool calls).
"""

from __future__ import annotations

import json

import railtracks as rt

from src.agents.schemas import FollowerVariationBatch

follower_llm = rt.llm.OpenAILLM("gpt-4.1-mini")

follower_variation_agent = rt.agent_node(
    name="follower-variation-generator",
    llm=follower_llm,
    system_message=(
        "Given an archetype's action plan and follower list, generate per-follower variations.\n"
        "For each follower output: happiness_delta (scaled by their volatility, range -0.2 to +0.2), "
        "tweet_text (only ~10% of followers should tweet — keep it short and personality-driven), "
        "and position ([lat, lng] only if the follower is at a location noticeably different from "
        "their current position — leave null for most followers).\n"
        "Minimize output: null fields take no tokens. Only include tweet_text and position when "
        "they meaningfully apply."
    ),
    output_schema=FollowerVariationBatch,
)


def build_follower_variation_prompt(archetype, archetype_response, followers):
    """Build the user message with all context pre-loaded for gpt-4.1-mini.

    Parameters
    ----------
    archetype : Archetype
        The SQLAlchemy archetype model instance.
    archetype_response : ArchetypeResponse
        The validated response from the Tier 1 agent.
    followers : list[Follower]
        All followers belonging to this archetype.

    Returns
    -------
    str
        The fully-formed user message containing all context the Tier 2
        agent needs to produce variations.
    """
    actions_json = json.dumps(
        [a.model_dump() for a in archetype_response.actions]
    )
    followers_json = json.dumps(
        [
            {
                "follower_id": f.follower_id,
                "name": f.name,
                "volatility": f.volatility,
                "happiness": f.happiness,
                "position": f.position,
            }
            | ({"ailments": f.status_ailments} if f.status_ailments else {})
            for f in followers
        ]
    )

    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    work = getattr(archetype, "work_district", None) or archetype.region

    return (
        f"Archetype: {archetype.industry} workers living in {home}, working in {work}\n"
        f"Archetype actions for this tick:\n{actions_json}\n\n"
        f"Followers to generate variations for:\n{followers_json}\n\n"
        "Generate one variation per follower. For each follower:\n"
        "- happiness_delta: scaled by their volatility "
        "(multiply a small base delta -0.1 to +0.1 by their volatility)\n"
        "- tweet_text: ~10% of followers should have a tweet "
        "(short, personality-driven)\n"
        "- position: only if the follower has moved somewhere distinctly different (omit for most)\n"
    )
