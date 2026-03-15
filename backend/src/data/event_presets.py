"""
Tunable preset reference examples for the event designer agent.

These are NOT user-facing — they serve as few-shot examples in the agent's
system prompt so it knows how to translate free-form narrative into structured
mechanical effects.  Devs tune the numbers here to calibrate the agent's
output patterns.
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Valid values (must match the simulation's canonical names)
# ---------------------------------------------------------------------------

VALID_INDUSTRIES = ["Finance", "Tech", "Healthcare", "Retail", "Government", "Education"]

VALID_NEIGHBORHOODS = [
    "Liberty Village / Exhibition",
    "Queen West / Trinity-Bellwoods",
    "Entertainment / Harbourfront",
    "Chinatown / Kensington",
    "Financial / St. Lawrence",
    "Downtown Yonge / Church-Wellesley",
    "Corktown / Distillery",
    "Cabbagetown / Regent Park",
]

VALID_WORK_DISTRICTS = [
    "Financial District",
    "Entertainment District",
    "Tech Corridor",
    "UofT District",
    "TMU District",
    "Government District",
    "Hospital Row",
    "CNE / Exhibition Place",
]

# ---------------------------------------------------------------------------
# Effect lever descriptions — injected into the agent system prompt
# ---------------------------------------------------------------------------

EFFECTS_LEVER_DESCRIPTION = """\
You have the following effect levers.  Set only the ones relevant to the event; \
leave the rest null.

stay_home_rate (float | null, 0.0–1.0)
  Override the fraction of people who stay home instead of commuting.
  Default simulation value is 0.15.  0.80 = severe lockdown.

happiness_delta (float | null, -0.3 to +0.3)
  Global per-tick happiness modifier applied to ALL followers.

happiness_per_industry (list | null, e.g. [{"industry": "Tech", "value": -0.15}])
  Additional per-industry happiness modifier (stacks with global).

tweet_rate_multiplier (float | null, 1.0–5.0)
  Multiplier on the base 10% tweet rate.  2.0 = twice as many tweets.

tweet_sentiment (string | null)
  One-word mood hint for tweet generation, e.g. "fearful", "angry",
  "celebratory", "frustrated", "excited", "anxious", "ecstatic".

disease_transmission_multiplier (float | null, 0.1–10.0)
  Multiplier on daily disease transmission rates.  3.0 = triple spread.

gathering_zones (list | null)
  Zones that attract people.  Each entry:
  {"zone_name": "<name>", "pull_strength": 0.0–1.0, "start_hour": 0–23 | null, "end_hour": 0–23 | null}.
  pull_strength is the fraction of the population drawn to that zone.
  start_hour/end_hour restrict when the gathering is active.  Defaults to 9–16 if omitted.
  Set start_hour == end_hour (e.g. 0, 0) for true 24/7 (only for emergencies/disasters).
  Typical windows: protests 9–18, celebrations 14–23, festivals 10–22, rallies 9–17,
  nightlife 20–2, markets 8–18.  Wrap past midnight is supported (e.g. start_hour=20, end_hour=2).

industry_stay_home (list | null, e.g. [{"industry": "Tech", "value": 0.70}])
  Per-industry stay-home rate overrides (0.0 = everyone works, 1.0 = all stay home).
  Use this to make essential workers keep working (e.g. [{"industry": "Healthcare", "value": 0.05}]).

duration_ticks (int | null)
  How many hourly ticks this event lasts.  null = permanent.
  24 = 1 day, 48 = 2 days, 168 = 1 week.

reasoning (string, required)
  1-2 sentence explanation of why you chose these effects.
"""

# ---------------------------------------------------------------------------
# Few-shot preset examples — narrative → effects
# ---------------------------------------------------------------------------

EVENT_PRESET_EXAMPLES: list[dict] = [
    {
        "narrative": "A severe pandemic outbreak has been declared in Toronto. Hospitals are overwhelmed and the government has issued a stay-at-home order.",
        "effects": {
            "stay_home_rate": 0.80,
            "happiness_delta": -0.15,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 2.5,
            "tweet_sentiment": "fearful",
            "disease_transmission_multiplier": 3.0,
            "gathering_zones": [{"zone_name": "Hospital Row", "pull_strength": 0.15, "start_hour": 0, "end_hour": 0}],
            "industry_stay_home": [{"industry": "Healthcare", "value": 0.05}, {"industry": "Government", "value": 0.20}],
            "duration_ticks": 168,
            "reasoning": "Pandemic causes mass stay-at-home behavior. Healthcare workers remain essential and cluster at hospitals. Disease spreads rapidly and social media floods with fear.",
        },
    },
    {
        "narrative": "A major economic crash sends shockwaves through Toronto's financial sector. Markets are in free-fall and protests are forming downtown.",
        "effects": {
            "stay_home_rate": 0.30,
            "happiness_delta": -0.12,
            "happiness_per_industry": [{"industry": "Finance", "value": -0.04}],
            "tweet_rate_multiplier": 2.5,
            "tweet_sentiment": "angry",
            "disease_transmission_multiplier": None,
            "gathering_zones": [{"zone_name": "Financial District", "pull_strength": 0.3, "start_hour": 9, "end_hour": 18}],
            "industry_stay_home": None,
            "duration_ticks": 72,
            "reasoning": "Economic crash drives daytime protests to the Financial District. Unhappiness spikes, especially in finance. Many stay home in uncertainty.",
        },
    },
    {
        "narrative": "An unexpected economic boom sweeps through Toronto. Companies report record profits and bonuses are flowing.",
        "effects": {
            "stay_home_rate": None,
            "happiness_delta": 0.10,
            "happiness_per_industry": [{"industry": "Finance", "value": 0.04}],
            "tweet_rate_multiplier": 2.0,
            "tweet_sentiment": "celebratory",
            "disease_transmission_multiplier": None,
            "gathering_zones": [{"zone_name": "Financial District", "pull_strength": 0.2, "start_hour": 15, "end_hour": 23}],
            "industry_stay_home": None,
            "duration_ticks": 48,
            "reasoning": "Economic prosperity boosts happiness. Finance workers celebrate near offices after work. Social media buzzes with good news.",
        },
    },
    {
        "narrative": "Toronto erupts in celebration as a massive city festival takes over the waterfront and entertainment district.",
        "effects": {
            "stay_home_rate": None,
            "happiness_delta": 0.10,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 2.0,
            "tweet_sentiment": "excited",
            "disease_transmission_multiplier": None,
            "gathering_zones": [
                {"zone_name": "Entertainment District", "pull_strength": 0.4, "start_hour": 10, "end_hour": 23},
                {"zone_name": "Entertainment / Harbourfront", "pull_strength": 0.3, "start_hour": 10, "end_hour": 23},
            ],
            "industry_stay_home": None,
            "duration_ticks": 24,
            "reasoning": "Festival draws large crowds to entertainment areas from morning through late evening. Mood is positive and social media buzzes.",
        },
    },
    {
        "narrative": "The TTC has gone on strike, paralyzing Toronto's public transit system. Most workers cannot get to their offices.",
        "effects": {
            "stay_home_rate": 0.60,
            "happiness_delta": -0.10,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 2.5,
            "tweet_sentiment": "frustrated",
            "disease_transmission_multiplier": None,
            "gathering_zones": [{"zone_name": "Government District", "pull_strength": 0.15, "start_hour": 8, "end_hour": 18}],
            "industry_stay_home": [{"industry": "Healthcare", "value": 0.10}, {"industry": "Government", "value": 0.20}],
            "duration_ticks": 24,
            "reasoning": "Transit strike strands most commuters at home. Daytime protesters gather at Government District. Healthcare and government workers find ways to get to work.",
        },
    },
    {
        "narrative": "A catastrophic ice storm has blanketed Toronto in ice. Power outages are widespread and roads are impassable.",
        "effects": {
            "stay_home_rate": 0.85,
            "happiness_delta": -0.10,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 2.0,
            "tweet_sentiment": "anxious",
            "disease_transmission_multiplier": None,
            "gathering_zones": None,
            "industry_stay_home": [{"industry": "Healthcare", "value": 0.05}, {"industry": "Government", "value": 0.10}],
            "duration_ticks": 36,
            "reasoning": "Ice storm forces nearly everyone indoors. Social media lights up with power outage reports. Only essential workers venture out.",
        },
    },
    {
        "narrative": "Multiple major tech companies have announced sweeping layoffs in Toronto. Thousands of software engineers are out of work.",
        "effects": {
            "stay_home_rate": None,
            "happiness_delta": -0.05,
            "happiness_per_industry": [{"industry": "Tech", "value": -0.10}],
            "tweet_rate_multiplier": 2.5,
            "tweet_sentiment": "anxious",
            "disease_transmission_multiplier": None,
            "gathering_zones": [{"zone_name": "Tech Corridor", "pull_strength": 0.15, "start_hour": 10, "end_hour": 17}],
            "industry_stay_home": [{"industry": "Tech", "value": 0.70}],
            "duration_ticks": 48,
            "reasoning": "Tech layoffs devastate the industry. Laid-off workers stay home while some gather near tech offices. Social media floods with layoff stories.",
        },
    },
    {
        "narrative": "A major social movement rally is taking place at Queen's Park, drawing thousands of protesters from across the city.",
        "effects": {
            "stay_home_rate": None,
            "happiness_delta": 0.05,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 3.0,
            "tweet_sentiment": "passionate",
            "disease_transmission_multiplier": None,
            "gathering_zones": [
                {"zone_name": "Government District", "pull_strength": 0.35, "start_hour": 9, "end_hour": 18},
                {"zone_name": "Downtown Yonge / Church-Wellesley", "pull_strength": 0.15, "start_hour": 9, "end_hour": 18},
            ],
            "industry_stay_home": None,
            "duration_ticks": 12,
            "reasoning": "Rally draws large daytime crowds to Queen's Park and spills into Downtown Yonge. Social media engagement spikes.",
        },
    },
    {
        "narrative": "An extreme heatwave grips Toronto with temperatures exceeding 40°C. Heat warnings are in effect.",
        "effects": {
            "stay_home_rate": 0.40,
            "happiness_delta": -0.08,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 2.0,
            "tweet_sentiment": "uncomfortable",
            "disease_transmission_multiplier": 0.5,
            "gathering_zones": [{"zone_name": "Entertainment / Harbourfront", "pull_strength": 0.15, "start_hour": 11, "end_hour": 20}],
            "industry_stay_home": [{"industry": "Healthcare", "value": 0.05}],
            "duration_ticks": 48,
            "reasoning": "Heatwave keeps many indoors. Some flock to the waterfront for relief. Healthcare workers stay essential. Disease drops as people isolate in AC.",
        },
    },
    {
        "narrative": "Toronto has won the championship! The city erupts in celebration as fans flood the streets downtown.",
        "effects": {
            "stay_home_rate": None,
            "happiness_delta": 0.15,
            "happiness_per_industry": None,
            "tweet_rate_multiplier": 3.0,
            "tweet_sentiment": "ecstatic",
            "disease_transmission_multiplier": None,
            "gathering_zones": [
                {"zone_name": "Entertainment District", "pull_strength": 0.5, "start_hour": 14, "end_hour": 2},
                {"zone_name": "Downtown Yonge / Church-Wellesley", "pull_strength": 0.3, "start_hour": 14, "end_hour": 2},
            ],
            "industry_stay_home": None,
            "duration_ticks": 12,
            "reasoning": "Championship win causes massive celebration from afternoon through the night. Fans flood Entertainment District and Yonge Street.",
        },
    },
]


def build_few_shot_examples() -> str:
    """Format preset examples as few-shot prompt text for the event designer agent."""
    lines: list[str] = []
    for i, ex in enumerate(EVENT_PRESET_EXAMPLES, 1):
        effects_json = json.dumps(ex["effects"], indent=2)
        lines.append(
            f"Example {i}:\n"
            f"Narrative: \"{ex['narrative']}\"\n"
            f"Effects:\n{effects_json}\n"
        )
    return "\n".join(lines)
