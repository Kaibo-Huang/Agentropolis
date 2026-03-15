"""
Tweet generation agent — LLM only for tweet text.

Happiness and position are computed by rule-based logic in follower_rules.py.
This agent only generates tweet_text for the ~10% of followers selected to tweet.
"""
from __future__ import annotations

import json

import railtracks as rt

from src.agents.schemas import TweetBatch

follower_llm = rt.llm.OpenAILLM("gpt-4.1-mini")

tweet_agent = rt.agent_node(
    name="follower-tweet-generator",
    llm=follower_llm,
    system_message=(
        "Generate a short, personality-driven tweet for each follower based on their "
        "archetype's current actions. Keep tweets under 140 characters. "
        "Write in first person. Reflect the follower's name and any ailments. "
        "Make it feel human — varied tone, occasional humour or frustration."
    ),
    output_schema=TweetBatch,
)


def build_tweet_prompt(archetype, archetype_response, tweeters: list) -> str:
    """Build a minimal prompt for tweet generation."""
    actions_summary = ", ".join(
        f"{a.action_type}({a.duration}h)" for a in archetype_response.actions
    )
    followers_json = json.dumps([
        {"follower_id": f.follower_id, "name": f.name}
        | ({"ailments": f.status_ailments} if f.status_ailments else {})
        for f in tweeters
    ])
    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    return (
        f"Archetype: {archetype.industry} workers in {home}\n"
        f"Actions this tick: {actions_summary}\n\n"
        f"Write one tweet for each follower:\n{followers_json}"
    )
