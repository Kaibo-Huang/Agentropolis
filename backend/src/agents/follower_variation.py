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
        "- Mix opening styles: question, reaction, observation, action, quote-like fragment\n"
        "- Avoid the template 'Name, ...'; prefer natural conversation\n\n"
        "When major events are happening: be DIRECT and SPECIFIC about the event. "
        "Don't vaguely allude to 'the mood' or 'the city's fear' — name what's happening. "
        "Example for pandemic: 'Can't believe they're making us go to work during a literal outbreak' "
        "NOT 'the city feels tense today'."
    ),
    output_schema=TweetBatch,
)


def _describe_gathering_zones(gathering_zones: list[dict], hour: int) -> str:
    """Build a human-readable description of gathering zones and their timing status."""
    if not gathering_zones:
        return ""
    lines = []
    for gz in gathering_zones:
        name = gz.get("zone_name", "unknown")
        s = gz.get("start_hour", 9)
        e = gz.get("end_hour", 16)
        is_24_7 = (s == e)
        if is_24_7:
            active = True
        elif s < e:
            active = s <= hour < e
        else:
            active = hour >= s or hour < e

        if active:
            lines.append(f"  - {name}: ACTIVE NOW — crowds are gathering there")
        else:
            # Describe when it starts/ends
            if s < e:
                if hour < s:
                    lines.append(f"  - {name}: starts at {s}:00 — people are anticipating, heading over soon")
                else:
                    lines.append(f"  - {name}: ended at {e}:00 — crowds dispersing, people reflecting")
            else:  # wraps midnight
                if hour < e:
                    lines.append(f"  - {name}: ends at {e}:00 — still winding down")
                else:
                    lines.append(f"  - {name}: starts at {s}:00 — people are anticipating, making plans")
    return "\n".join(lines)


def build_tweet_prompt(
    archetype,
    archetype_response,
    tweeters: list,
    tweet_sentiment: str | None = None,
    event_prompts: list[str] | None = None,
    gathering_zones: list[dict] | None = None,
    hour: int = 12,
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

        # Gathering zone status — tells LLM what's happening WHERE and WHEN
        zone_block = ""
        if gathering_zones:
            zone_desc = _describe_gathering_zones(gathering_zones, hour)
            zone_block = f"\nGATHERING LOCATIONS:\n{zone_desc}\n"

        hour_label = f"{hour}:00" if hour >= 10 else f"0{hour}:00"
        event_block = (
            f"\nCurrent time: {hour_label}\n"
            f"MAJOR EVENTS IN TORONTO:\n{event_lines}\n"
            f"{zone_block}"
            f"{mood_line}\n"
            "Tweets MUST directly reference what's happening — be specific about the event AND location.\n"
            "If a gathering is about to start, tweet about heading there, anticipation, seeing crowds build.\n"
            "If it's active, tweet about being there or watching the scene unfold.\n"
            "If it ended, tweet about aftermath, what happened, what you saw.\n"
            "Each tweet should take a DIFFERENT angle: personal story, hot take, "
            "complaint, dark humor, news reaction, fear, anger, sarcasm, hope.\n"
        )

    return (
        f"{industry} workers living in {home}\n"
        f"What they did this tick: {actions_summary}\n"
        f"{event_block}\n"
        "Batch-level style constraints:\n"
        "- Vary the first 3-5 words across tweets; avoid repeated lead-ins\n"
        "- If this batch has 2+ tweets, at most one may start with a name\n"
        "- Names are optional; do not default to 'Name, ...' openings\n"
        f"Write one unique tweet per follower using follower_id mapping:\n{followers_json}"
    )
