"""
Disease configuration data for Agentropolis simulation.

Each entry may include:
  name (str): disease identifier
  transmission_rate_per_day (float): daily probability of spreading to a contact (contagious diseases)
  incidence_rate_per_day (float): daily background incidence rate (non-contagious diseases)
  is_contagious (bool): whether the disease spreads between followers
"""

DISEASE_CONFIGS: list[dict] = [
    {
        "name": "flu",
        "transmission_rate_per_day": 0.05,
        "is_contagious": True,
    },
    {
        "name": "covid",
        "transmission_rate_per_day": 0.08,
        "is_contagious": True,
    },
    {
        "name": "cancer",
        "incidence_rate_per_day": 0.0001,
        "is_contagious": False,
    },
]
