"""
Event designer agent — translates free-form narrative into structured
mechanical effects for the simulation.

Called once at injection time (not per-tick).  Uses tunable preset examples
as few-shot references so the agent knows how to map narratives to effects.
"""

from __future__ import annotations

import json
import logging

import railtracks as rt

from src.agents.schemas import EventEffects
from src.data.event_presets import (
    EFFECTS_LEVER_DESCRIPTION,
    VALID_INDUSTRIES,
    VALID_NEIGHBORHOODS,
    VALID_WORK_DISTRICTS,
    build_few_shot_examples,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# System prompt (built once at import time)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = f"""\
You are an event designer for a Toronto population simulation called Agentropolis.

Your job: translate a user's free-form narrative event description into structured \
mechanical effects that the simulation engine applies each tick.

SIMULATION CONTEXT:
- Population of ~256 followers across 40 archetypes in downtown Toronto.
- 6 industries: {", ".join(VALID_INDUSTRIES)}
- 8 residential neighborhoods: {", ".join(VALID_NEIGHBORHOODS)}
- 8 work districts: {", ".join(VALID_WORK_DISTRICTS)}
- Default: 15% of people stay home, 10% tweet each tick, happiness range 0.0-1.0.

AVAILABLE EFFECT LEVERS:
{EFFECTS_LEVER_DESCRIPTION}

GUIDELINES:
- Only set levers that are relevant to the event. Leave the rest null.
- Be realistic about magnitudes — a minor local event shouldn't have 0.80 stay_home_rate.
- Consider which populations are most affected (industry targeting, specific zones).
- gathering_zones zone_name MUST exactly match one of the valid neighborhoods or work districts listed above.
- industry_stay_home and happiness_per_industry "industry" values MUST exactly match one of the valid industries.
- Always provide a reasoning field explaining your choices.

REFERENCE EXAMPLES:
{build_few_shot_examples()}
Use these examples as calibration — draw inspiration from similar scenarios, \
but tailor effects to the specific narrative provided."""

# ---------------------------------------------------------------------------
# Agent node
# ---------------------------------------------------------------------------

event_designer_llm = rt.llm.OpenAILLM("gpt-4.1-mini")

event_designer_agent = rt.agent_node(
    name="event-designer",
    llm=event_designer_llm,
    system_message=_SYSTEM_PROMPT,
    output_schema=EventEffects,
)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def build_event_designer_prompt(
    narrative: str,
    existing_events: list[str] | None = None,
) -> str:
    """Build the user message for the event designer agent.

    Parameters
    ----------
    narrative : str
        The user's free-form event description.
    existing_events : list[str] | None
        Summaries of currently active events (world history context).
    """
    parts = [f'Event narrative: "{narrative}"']

    if existing_events:
        history = json.dumps(existing_events[:10])  # cap at 10 for context length
        parts.append(
            f"\nCurrently active events in the simulation:\n{history}\n"
            "Consider how this new event interacts with or compounds existing events."
        )

    parts.append(
        "\nGenerate the structured effects for this event. "
        "Set only the relevant levers; leave the rest null."
    )

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Call helper with retry + fallback
# ---------------------------------------------------------------------------


async def design_event_effects(
    narrative: str,
    session_id: str,
    existing_events: list[str] | None = None,
) -> dict | None:
    """Call the event designer agent and return effects as a dict.

    Returns None if all retries fail (event will be stored as narrative-only).
    """
    user_msg = build_event_designer_prompt(narrative, existing_events)

    for attempt in range(MAX_RETRIES):
        try:
            with rt.Session(
                name=f"event-design-{session_id}",
                timeout=15.0,
                save_state=False,
            ):
                result = await rt.call(event_designer_agent, user_msg)
                effects = result.structured
                logger.info(
                    "Event designer attempt %d succeeded: %s",
                    attempt + 1,
                    effects.reasoning,
                )
                return effects.model_dump()
        except Exception as e:
            logger.warning(
                "Event designer attempt %d failed: %s",
                attempt + 1,
                e,
            )

    logger.error("Event designer: all %d retries failed, storing as narrative-only", MAX_RETRIES)
    return None
