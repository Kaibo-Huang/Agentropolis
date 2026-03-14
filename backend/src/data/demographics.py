"""
Toronto demographic distributions for Agentropolis follower generation.

All distribution dicts are intended for use with random.choices(population, weights=...).
Weights do not need to sum to exactly 1.0 — random.choices normalises them.
"""

# ---------------------------------------------------------------------------
# Social classes
# ---------------------------------------------------------------------------

SOCIAL_CLASSES: list[str] = ["lower", "middle", "upper"]

# Per-region weights for social class assignment.
# Order matches SOCIAL_CLASSES: [lower, middle, upper]
SOCIAL_CLASS_WEIGHTS_BY_REGION: dict[str, list[float]] = {
    "Downtown Core": [0.20, 0.50, 0.30],
    "Financial District": [0.05, 0.35, 0.60],
    "Entertainment District": [0.15, 0.55, 0.30],
    "Midtown": [0.15, 0.50, 0.35],
    "North York": [0.25, 0.55, 0.20],
    "Scarborough": [0.35, 0.50, 0.15],
    "Etobicoke": [0.28, 0.52, 0.20],
    "Waterfront": [0.10, 0.45, 0.45],
    "Yorkville": [0.05, 0.25, 0.70],
    "Liberty Village": [0.12, 0.58, 0.30],
    "Queen's Park": [0.10, 0.50, 0.40],
    "University District": [0.30, 0.55, 0.15],
}

# Default weights used when a region is not in the map above
DEFAULT_SOCIAL_CLASS_WEIGHTS: list[float] = [0.25, 0.50, 0.25]

# ---------------------------------------------------------------------------
# Social class weights by *residential neighborhood* (new zoning system)
# Order matches SOCIAL_CLASSES: [lower, middle, upper]
# ---------------------------------------------------------------------------

SOCIAL_CLASS_WEIGHTS_BY_NEIGHBORHOOD: dict[str, list[float]] = {
    "Liberty Village / Exhibition": [0.12, 0.58, 0.30],
    "Queen West / Trinity-Bellwoods": [0.18, 0.52, 0.30],
    "Entertainment / Harbourfront": [0.15, 0.50, 0.35],
    "Chinatown / Kensington": [0.25, 0.55, 0.20],
    "Financial / St. Lawrence": [0.08, 0.40, 0.52],
    "Downtown Yonge / Church-Wellesley": [0.20, 0.50, 0.30],
    "Corktown / Distillery": [0.22, 0.55, 0.23],
    "Cabbagetown / Regent Park": [0.30, 0.52, 0.18],
}

# ---------------------------------------------------------------------------
# Age distribution
# ---------------------------------------------------------------------------

# (min_age, max_age, weight) tuples
AGE_DISTRIBUTION: list[tuple[int, int, float]] = [
    (18, 24, 0.15),
    (25, 34, 0.25),
    (35, 44, 0.22),
    (45, 54, 0.18),
    (55, 64, 0.12),
    (65, 80, 0.08),
]

# ---------------------------------------------------------------------------
# Gender distribution
# ---------------------------------------------------------------------------

GENDER_DISTRIBUTION: dict[str, float] = {
    "male": 0.49,
    "female": 0.49,
    "non-binary": 0.02,
}

# ---------------------------------------------------------------------------
# Race/ethnicity distribution (approximate Toronto Census data)
# ---------------------------------------------------------------------------

RACE_DISTRIBUTION: dict[str, float] = {
    "White": 0.47,
    "South Asian": 0.12,
    "East Asian": 0.11,
    "Black": 0.09,
    "Southeast Asian": 0.05,
    "Latin American": 0.04,
    "Arab": 0.03,
    "Filipino": 0.03,
    "West Asian": 0.02,
    "Indigenous": 0.01,
    "Other": 0.03,
}

# ---------------------------------------------------------------------------
# Name lists — diverse, reflecting Toronto's multicultural population
# ---------------------------------------------------------------------------

FIRST_NAMES: list[str] = [
    # English / Western
    "James",
    "Sarah",
    "Michael",
    "Emily",
    "David",
    "Jessica",
    "Daniel",
    "Ashley",
    "Matthew",
    "Lauren",
    "Christopher",
    "Megan",
    "Andrew",
    "Nicole",
    "Joshua",
    "Stephanie",
    "Ryan",
    "Amanda",
    "Tyler",
    "Jennifer",
    # South Asian
    "Arjun",
    "Priya",
    "Rahul",
    "Ananya",
    "Vikram",
    "Divya",
    "Rohan",
    "Nisha",
    "Amit",
    "Kavya",
    # East Asian
    "Wei",
    "Mei",
    "Jun",
    "Ying",
    "Hao",
    "Xin",
    "Yuki",
    "Kenji",
    "Haruto",
    "Sakura",
    # South / Southeast Asian / Filipino
    "Jose",
    "Maria",
    "Miguel",
    "Ana",
    "Carlos",
    "Sofia",
    "Juan",
    "Isabella",
    # African / Caribbean / Black
    "Kwame",
    "Amara",
    "Kofi",
    "Fatima",
    "Tariq",
    "Aisha",
    "Jalen",
    "Zara",
    # Middle Eastern / Arab
    "Omar",
    "Layla",
    "Hassan",
    "Yasmin",
    "Ali",
    "Nadia",
    # Indigenous / Other
    "River",
    "Jordan",
    "Taylor",
    "Morgan",
    "Alex",
    "Sam",
    "Quinn",
    "Riley",
]

LAST_NAMES: list[str] = [
    # English / Western
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Wilson",
    "Taylor",
    "Anderson",
    "Thomas",
    "Jackson",
    "White",
    "Harris",
    "Martin",
    "Thompson",
    "Garcia",
    "Martinez",
    "Robinson",
    "Clark",
    # South Asian
    "Patel",
    "Sharma",
    "Singh",
    "Kumar",
    "Gupta",
    "Shah",
    "Mehta",
    "Joshi",
    "Verma",
    "Nair",
    # East Asian
    "Wang",
    "Li",
    "Zhang",
    "Chen",
    "Liu",
    "Yang",
    "Huang",
    "Kim",
    "Park",
    "Tanaka",
    # South / Southeast Asian
    "Santos",
    "Cruz",
    "Reyes",
    "Flores",
    "Rivera",
    "Torres",
    "Nguyen",
    "Tran",
    "Le",
    "Pham",
    # African / Caribbean
    "Okafor",
    "Mensah",
    "Asante",
    "Diallo",
    "Nkrumah",
    "Baptiste",
    "Joseph",
    "Pierre",
    # Middle Eastern
    "Hassan",
    "Ahmed",
    "Ali",
    "Khan",
    "Malik",
    "Rahman",
    # Other / Mixed
    "Murray",
    "Fraser",
    "MacDonald",
    "Campbell",
    "Stewart",
]
