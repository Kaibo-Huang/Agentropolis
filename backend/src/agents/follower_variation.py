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
        "Generate a short tweet for each follower. Under 140 characters. First person.\n\n"
        "VARIETY IS CRITICAL — every tweet must feel different:\n"
        "- Vary the angle: some angry, some scared, some sarcastic, some hopeful, some joking\n"
        "- Vary the topic: personal impact, hot take, news reaction, complaint, dark humor\n"
        "- NEVER repeat the same phrasing or structure across tweets\n"
        "- Use the follower's first name naturally (not 'Follower #X')\n\n"
        "When major events are happening: be DIRECT and SPECIFIC about the event. "
        "Don't vaguely allude to 'the mood' or 'the city's fear' — name what's happening. "
        "Example for pandemic: 'Can't believe they're making us go to work during a literal outbreak' "
        "NOT 'the city feels tense today'."
    ),
    output_schema=TweetBatch,
)


def build_tweet_prompt(
    archetype,
    archetype_response,
    tweeters: list,
    tweet_sentiment: str | None = None,
    event_prompts: list[str] | None = None,
) -> str:
    """Build the tweet generation prompt.

    When major events are active, the prompt foregrounds them so the LLM
    generates event-reactive tweets rather than mundane daily-life content.
    Each follower gets unique context (happiness, neighborhood) for variety.
    """
    actions_summary = ", ".join(
        f"{a.action_type}({a.duration}h)" for a in archetype_response.actions
    )
    # Rich per-follower context for variety
    followers_data = []
    for f in tweeters:
        entry: dict = {
            "follower_id": f.follower_id,
            "name": f.name,
            "happiness": round(f.happiness, 2),
        }
        if f.status_ailments:
            entry["ailments"] = f.status_ailments
        followers_data.append(entry)
    followers_json = json.dumps(followers_data)

    home = getattr(archetype, "home_neighborhood", None) or archetype.region
    industry = getattr(archetype, "industry", "unknown")

    # Build event context block — this is the PRIMARY tweet driver when events exist
    event_block = ""
    if event_prompts:
        event_lines = "\n".join(f"- {ep}" for ep in event_prompts[-5:])
        mood_line = f"City mood: {tweet_sentiment}.\n" if tweet_sentiment else ""
        event_block = (
            f"\nMAJOR EVENTS IN TORONTO RIGHT NOW:\n{event_lines}\n"
            f"{mood_line}\n"
            "Tweets MUST directly reference what's happening — be specific.\n"
            "Each tweet should take a DIFFERENT angle: personal story, hot take, "
            "complaint, dark humor, news reaction, fear, anger, sarcasm, hope.\n"
            "Do NOT vaguely say 'the city feels tense' — say what you actually mean.\n"
        )

    return (
        f"{industry} workers living in {home}\n"
        f"What they did this tick: {actions_summary}\n"
        f"{event_block}\n"
        f"Write one unique tweet per follower (use their first name, not ID):\n{followers_json}"
    )
