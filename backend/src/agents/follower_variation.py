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
        "Given an archetype's action plan and follower details, generate slight variations.\n"
        "Vary: timing offsets (+-15 min), minor location differences (same region),\n"
        "whether they post a tweet (~10% should), happiness delta scaled by their volatility.\n"
        "Return JSON array of follower updates."
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

    return (
        f"Archetype: {archetype.industry} workers in {archetype.region}\n"
        f"Archetype actions for this tick:\n{actions_json}\n\n"
        f"Followers to generate variations for:\n{followers_json}\n\n"
        "Generate one variation per follower. For each follower:\n"
        "- timing_offset_minutes: small offset (-15 to +15)\n"
        "- happiness_delta: scaled by their volatility "
        "(multiply a small base delta -0.1 to +0.1 by their volatility)\n"
        "- tweet_text: ~10% of followers should have a tweet "
        "(short, personality-driven)\n"
        "- position: [lat, lng] if different from archetype default\n"
    )
