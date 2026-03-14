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
