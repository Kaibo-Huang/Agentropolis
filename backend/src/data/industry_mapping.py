"""
Industry-to-region mapping, employer list, and home-neighborhood weights
for Agentropolis.

EMPLOYERS: fixed list of 20 Toronto employers, each with industry and work district.
INDUSTRIES: flat list of all industry names.
INDUSTRY_HOME_WEIGHTS: per-industry residential neighborhood weights.
"""

# ---------------------------------------------------------------------------
# Fixed employer list — archetypes cycle through this in order
# ---------------------------------------------------------------------------

EMPLOYERS: list[dict[str, str]] = [
    {"name": "Ontario Government",  "industry": "Government",  "work_district": "Government District"},
    {"name": "Toronto Government",  "industry": "Government",  "work_district": "Government District"},
    {"name": "Vector Institute",    "industry": "Tech",         "work_district": "UofT District"},
    {"name": "Bitdeer AI",          "industry": "Tech",         "work_district": "UofT District"},
    {"name": "TDSB",                "industry": "Education",    "work_district": "TMU District"},
    {"name": "Eaton Centre",        "industry": "Retail",       "work_district": "TMU District"},
    {"name": "AMD",                 "industry": "Tech",         "work_district": "Tech Corridor"},
    {"name": "IBM",                 "industry": "Tech",         "work_district": "Tech Corridor"},
    {"name": "BMO",                 "industry": "Finance",      "work_district": "CNE / Exhibition Place"},
    {"name": "Shopify",             "industry": "Tech",         "work_district": "Entertainment District"},
    {"name": "Intuit",              "industry": "Tech",         "work_district": "Entertainment District"},
    {"name": "Small Businesses",    "industry": "Retail",       "work_district": "Entertainment District"},
    {"name": "Ontario Health",      "industry": "Healthcare",   "work_district": "Hospital Row"},
    {"name": "Hospital",            "industry": "Healthcare",   "work_district": "Hospital Row"},
    {"name": "TD",                  "industry": "Finance",      "work_district": "Financial District"},
    {"name": "RBC",                 "industry": "Finance",      "work_district": "Financial District"},
    {"name": "Sunlife",             "industry": "Finance",      "work_district": "Financial District"},
    {"name": "Google",              "industry": "Tech",         "work_district": "Financial District"},
    {"name": "Railtown",            "industry": "Tech",         "work_district": "Financial District"},
    {"name": "Eleven Labs",         "industry": "Tech",         "work_district": "Financial District"},
]

INDUSTRIES: list[str] = ["Finance", "Tech", "Healthcare", "Retail", "Government", "Education"]

# ---------------------------------------------------------------------------
# Per-industry weighting across the 8 residential neighborhoods.
# Keys are neighborhood names, values are relative weights (sum to ~1.0).
# Higher weight = more likely for workers in that industry to live there.
# ---------------------------------------------------------------------------

INDUSTRY_HOME_WEIGHTS: dict[str, dict[str, float]] = {
    "Finance": {
        "Liberty Village / Exhibition": 0.11,
        "Queen West / Trinity-Bellwoods": 0.12,
        "Entertainment / Harbourfront": 0.13,
        "Chinatown / Kensington": 0.11,
        "Financial / St. Lawrence": 0.15,
        "Downtown Yonge / Church-Wellesley": 0.14,
        "Corktown / Distillery": 0.12,
        "Cabbagetown / Regent Park": 0.12,
    },
    "Tech": {
        "Liberty Village / Exhibition": 0.14,
        "Queen West / Trinity-Bellwoods": 0.14,
        "Entertainment / Harbourfront": 0.12,
        "Chinatown / Kensington": 0.12,
        "Financial / St. Lawrence": 0.11,
        "Downtown Yonge / Church-Wellesley": 0.12,
        "Corktown / Distillery": 0.12,
        "Cabbagetown / Regent Park": 0.13,
    },
    "Healthcare": {
        "Liberty Village / Exhibition": 0.11,
        "Queen West / Trinity-Bellwoods": 0.12,
        "Entertainment / Harbourfront": 0.11,
        "Chinatown / Kensington": 0.14,
        "Financial / St. Lawrence": 0.11,
        "Downtown Yonge / Church-Wellesley": 0.14,
        "Corktown / Distillery": 0.13,
        "Cabbagetown / Regent Park": 0.14,
    },
    "Retail": {
        "Liberty Village / Exhibition": 0.12,
        "Queen West / Trinity-Bellwoods": 0.13,
        "Entertainment / Harbourfront": 0.12,
        "Chinatown / Kensington": 0.13,
        "Financial / St. Lawrence": 0.12,
        "Downtown Yonge / Church-Wellesley": 0.13,
        "Corktown / Distillery": 0.12,
        "Cabbagetown / Regent Park": 0.13,
    },
    "Government": {
        "Liberty Village / Exhibition": 0.11,
        "Queen West / Trinity-Bellwoods": 0.12,
        "Entertainment / Harbourfront": 0.12,
        "Chinatown / Kensington": 0.13,
        "Financial / St. Lawrence": 0.13,
        "Downtown Yonge / Church-Wellesley": 0.14,
        "Corktown / Distillery": 0.12,
        "Cabbagetown / Regent Park": 0.13,
    },
    "Education": {
        "Liberty Village / Exhibition": 0.11,
        "Queen West / Trinity-Bellwoods": 0.12,
        "Entertainment / Harbourfront": 0.11,
        "Chinatown / Kensington": 0.15,
        "Financial / St. Lawrence": 0.11,
        "Downtown Yonge / Church-Wellesley": 0.14,
        "Corktown / Distillery": 0.12,
        "Cabbagetown / Regent Park": 0.14,
    },
}
