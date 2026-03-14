"""
Industry-to-region mapping and distribution weights for Agentropolis.

INDUSTRY_REGIONS: maps each industry to the Toronto regions where it operates.
INDUSTRIES: flat list of all industry names.
INDUSTRY_DISTRIBUTION: approximate Toronto employment share per industry (sums to 1.0).
"""

INDUSTRY_REGIONS: dict[str, list[str]] = {
    "Finance": ["Financial District"],
    "Tech": ["Downtown Core", "Liberty Village"],
    "Healthcare": ["Midtown", "University District"],
    "Retail": [
        "Downtown Core",
        "North York",
        "Scarborough",
        "Etobicoke",
        "Midtown",
        "Yorkville",
    ],
    "Manufacturing": ["Etobicoke", "Scarborough"],
    "Government": ["Downtown Core", "Queen's Park"],
    "Education": ["University District", "Midtown"],
}

INDUSTRIES: list[str] = list(INDUSTRY_REGIONS.keys())

# Approximate Toronto employment distribution (sums to 1.0)
INDUSTRY_DISTRIBUTION: dict[str, float] = {
    "Finance": 0.15,
    "Tech": 0.18,
    "Healthcare": 0.12,
    "Retail": 0.20,
    "Manufacturing": 0.10,
    "Government": 0.10,
    "Education": 0.15,
}

# ---------------------------------------------------------------------------
# New zoning: industry → work district mapping
# ---------------------------------------------------------------------------

INDUSTRY_WORK_DISTRICTS: dict[str, list[str]] = {
    "Finance": ["Financial District"],
    "Tech": ["Tech Corridor"],
    "Healthcare": ["Hospital Row"],
    "Retail": ["Entertainment District", "Financial District"],
    "Manufacturing": ["Tech Corridor", "CNE / Exhibition Place"],
    "Government": ["Government District"],
    "Education": ["UofT District", "TMU District"],
}

# Per-industry weighting across the 8 residential neighborhoods.
# Keys are neighborhood names, values are relative weights (need not sum to 1).
# Higher weight = more likely for workers in that industry to live there.
INDUSTRY_HOME_WEIGHTS: dict[str, dict[str, float]] = {
    "Finance": {
        "Liberty Village / Exhibition": 0.10,
        "Queen West / Trinity-Bellwoods": 0.08,
        "Entertainment / Harbourfront": 0.18,
        "Chinatown / Kensington": 0.05,
        "Financial / St. Lawrence": 0.25,
        "Downtown Yonge / Church-Wellesley": 0.18,
        "Corktown / Distillery": 0.10,
        "Cabbagetown / Regent Park": 0.06,
    },
    "Tech": {
        "Liberty Village / Exhibition": 0.25,
        "Queen West / Trinity-Bellwoods": 0.20,
        "Entertainment / Harbourfront": 0.10,
        "Chinatown / Kensington": 0.12,
        "Financial / St. Lawrence": 0.05,
        "Downtown Yonge / Church-Wellesley": 0.10,
        "Corktown / Distillery": 0.10,
        "Cabbagetown / Regent Park": 0.08,
    },
    "Healthcare": {
        "Liberty Village / Exhibition": 0.08,
        "Queen West / Trinity-Bellwoods": 0.10,
        "Entertainment / Harbourfront": 0.08,
        "Chinatown / Kensington": 0.18,
        "Financial / St. Lawrence": 0.08,
        "Downtown Yonge / Church-Wellesley": 0.18,
        "Corktown / Distillery": 0.12,
        "Cabbagetown / Regent Park": 0.18,
    },
    "Retail": {
        "Liberty Village / Exhibition": 0.10,
        "Queen West / Trinity-Bellwoods": 0.15,
        "Entertainment / Harbourfront": 0.12,
        "Chinatown / Kensington": 0.15,
        "Financial / St. Lawrence": 0.10,
        "Downtown Yonge / Church-Wellesley": 0.15,
        "Corktown / Distillery": 0.10,
        "Cabbagetown / Regent Park": 0.13,
    },
    "Manufacturing": {
        "Liberty Village / Exhibition": 0.20,
        "Queen West / Trinity-Bellwoods": 0.12,
        "Entertainment / Harbourfront": 0.05,
        "Chinatown / Kensington": 0.08,
        "Financial / St. Lawrence": 0.03,
        "Downtown Yonge / Church-Wellesley": 0.08,
        "Corktown / Distillery": 0.22,
        "Cabbagetown / Regent Park": 0.22,
    },
    "Government": {
        "Liberty Village / Exhibition": 0.08,
        "Queen West / Trinity-Bellwoods": 0.10,
        "Entertainment / Harbourfront": 0.10,
        "Chinatown / Kensington": 0.15,
        "Financial / St. Lawrence": 0.15,
        "Downtown Yonge / Church-Wellesley": 0.18,
        "Corktown / Distillery": 0.10,
        "Cabbagetown / Regent Park": 0.14,
    },
    "Education": {
        "Liberty Village / Exhibition": 0.08,
        "Queen West / Trinity-Bellwoods": 0.12,
        "Entertainment / Harbourfront": 0.08,
        "Chinatown / Kensington": 0.22,
        "Financial / St. Lawrence": 0.05,
        "Downtown Yonge / Church-Wellesley": 0.20,
        "Corktown / Distillery": 0.10,
        "Cabbagetown / Regent Park": 0.15,
    },
}
