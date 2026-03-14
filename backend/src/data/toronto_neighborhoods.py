"""
Toronto neighborhood static data for the Agentropolis Location table.

TORONTO_NEIGHBORHOODS: list of dicts matching the Location model schema
    (name, type, region, position, metadata_)

NEIGHBORHOOD_BOUNDS: dict keyed by region name with bounding box values
    used for random position jitter when generating follower/company positions.
    Each entry: {"min_lat": float, "max_lat": float, "min_lng": float, "max_lng": float}

NOTE: NEIGHBORHOOD_BOUNDS is kept for backward compatibility.
New code should use toronto_zones.ALL_ZONE_BOUNDS instead.
"""

# ---------------------------------------------------------------------------
# Legacy bounding boxes — kept for backward compatibility.
# New code should import from toronto_zones.py instead.
# ---------------------------------------------------------------------------

NEIGHBORHOOD_BOUNDS: dict[str, dict[str, float]] = {
    "Downtown Core": {
        "min_lat": 43.6430,
        "max_lat": 43.6580,
        "min_lng": -79.3950,
        "max_lng": -79.3700,
    },
    "Financial District": {
        "min_lat": 43.6440,
        "max_lat": 43.6530,
        "min_lng": -79.3870,
        "max_lng": -79.3740,
    },
    "Entertainment District": {
        "min_lat": 43.6420,
        "max_lat": 43.6510,
        "min_lng": -79.4000,
        "max_lng": -79.3860,
    },
    "Midtown": {
        "min_lat": 43.6850,
        "max_lat": 43.7120,
        "min_lng": -79.4100,
        "max_lng": -79.3750,
    },
    "North York": {
        "min_lat": 43.7450,
        "max_lat": 43.7780,
        "min_lng": -79.4350,
        "max_lng": -79.3850,
    },
    "Scarborough": {
        "min_lat": 43.7480,
        "max_lat": 43.8100,
        "min_lng": -79.3000,
        "max_lng": -79.2100,
    },
    "Etobicoke": {
        "min_lat": 43.5950,
        "max_lat": 43.6600,
        "min_lng": -79.5500,
        "max_lng": -79.4800,
    },
    "Waterfront": {
        "min_lat": 43.6320,
        "max_lat": 43.6430,
        "min_lng": -79.3950,
        "max_lng": -79.3600,
    },
    "Yorkville": {
        "min_lat": 43.6680,
        "max_lat": 43.6760,
        "min_lng": -79.4000,
        "max_lng": -79.3870,
    },
    "Liberty Village": {
        "min_lat": 43.6330,
        "max_lat": 43.6430,
        "min_lng": -79.4280,
        "max_lng": -79.4130,
    },
    "Queen's Park": {
        "min_lat": 43.6560,
        "max_lat": 43.6660,
        "min_lng": -79.4000,
        "max_lng": -79.3870,
    },
    "University District": {
        "min_lat": 43.6580,
        "max_lat": 43.6690,
        "min_lng": -79.4010,
        "max_lng": -79.3880,
    },
}

# ---------------------------------------------------------------------------
# Neighborhood anchor points and landmarks
# Each dict maps directly to Location model columns:
#   name (str), type (str), region (str),
#   position ([lat, lng] as list), metadata_ (dict or None)
#
# `region` values use the new zone names from toronto_zones.py where
# the location falls within that zone's bounding box.
# ---------------------------------------------------------------------------

TORONTO_NEIGHBORHOODS: list[dict] = [
    # -----------------------------------------------------------------------
    # Financial / St. Lawrence neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Downtown Core",
        "type": "neighborhood",
        "region": "Financial / St. Lawrence",
        "position": [43.6510, -79.3832],
        "metadata_": {"description": "The central business and cultural hub of Toronto"},
    },
    {
        "name": "City Hall",
        "type": "landmark",
        "region": "Downtown Yonge / Church-Wellesley",
        "position": [43.6534, -79.3839],
        "metadata_": {"category": "government", "address": "100 Queen St W"},
    },
    {
        "name": "Eaton Centre",
        "type": "landmark",
        "region": "Downtown Yonge / Church-Wellesley",
        "position": [43.6544, -79.3807],
        "metadata_": {"category": "retail", "address": "220 Yonge St"},
    },
    {
        "name": "Nathan Phillips Square",
        "type": "landmark",
        "region": "Downtown Yonge / Church-Wellesley",
        "position": [43.6528, -79.3842],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Downtown Core Community Centre",
        "type": "building",
        "region": "Financial / St. Lawrence",
        "position": [43.6490, -79.3820],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "St. Patrick's Market",
        "type": "building",
        "region": "Financial / St. Lawrence",
        "position": [43.6515, -79.3855],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # Financial District (work district)
    # -----------------------------------------------------------------------
    {
        "name": "Financial District",
        "type": "district",
        "region": "Financial District",
        "position": [43.6483, -79.3808],
        "metadata_": {"description": "Toronto's primary banking and finance hub"},
    },
    {
        "name": "Toronto Stock Exchange",
        "type": "landmark",
        "region": "Financial District",
        "position": [43.6487, -79.3818],
        "metadata_": {"category": "office", "address": "130 King St W"},
    },
    {
        "name": "First Canadian Place",
        "type": "building",
        "region": "Financial District",
        "position": [43.6482, -79.3812],
        "metadata_": {"category": "office", "address": "100 King St W"},
    },
    {
        "name": "Scotia Plaza",
        "type": "building",
        "region": "Financial District",
        "position": [43.6478, -79.3800],
        "metadata_": {"category": "office", "address": "40 King St W"},
    },
    {
        "name": "Financial District Fitness Club",
        "type": "building",
        "region": "Financial District",
        "position": [43.6490, -79.3795],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "King Street Bistro",
        "type": "building",
        "region": "Financial District",
        "position": [43.6472, -79.3825],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # Entertainment District (work district)
    # -----------------------------------------------------------------------
    {
        "name": "Entertainment District",
        "type": "district",
        "region": "Entertainment District",
        "position": [43.6461, -79.3905],
        "metadata_": {"description": "Theatres, restaurants, and nightlife"},
    },
    {
        "name": "Rogers Centre",
        "type": "landmark",
        "region": "Entertainment District",
        "position": [43.6414, -79.3894],
        "metadata_": {"category": "stadium", "address": "1 Blue Jays Way"},
    },
    {
        "name": "Scotiabank Arena",
        "type": "landmark",
        "region": "Entertainment District",
        "position": [43.6435, -79.3791],
        "metadata_": {"category": "arena", "address": "40 Bay St"},
    },
    {
        "name": "Princess of Wales Theatre",
        "type": "landmark",
        "region": "Entertainment District",
        "position": [43.6471, -79.3907],
        "metadata_": {"category": "theatre", "address": "300 King St W"},
    },
    {
        "name": "Entertainment District Bar & Grill",
        "type": "building",
        "region": "Entertainment District",
        "position": [43.6458, -79.3920],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # Chinatown / Kensington neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Kensington Market",
        "type": "neighborhood",
        "region": "Chinatown / Kensington",
        "position": [43.6547, -79.4005],
        "metadata_": {"description": "Eclectic market neighbourhood with vintage shops and cafes"},
    },
    {
        "name": "Art Gallery of Ontario",
        "type": "landmark",
        "region": "Chinatown / Kensington",
        "position": [43.6536, -79.3925],
        "metadata_": {"category": "museum", "address": "317 Dundas St W"},
    },

    # -----------------------------------------------------------------------
    # Downtown Yonge / Church-Wellesley neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Dundas Square",
        "type": "landmark",
        "region": "Downtown Yonge / Church-Wellesley",
        "position": [43.6561, -79.3803],
        "metadata_": {"category": "park", "address": "Yonge-Dundas Square"},
    },
    {
        "name": "Allan Gardens",
        "type": "landmark",
        "region": "Downtown Yonge / Church-Wellesley",
        "position": [43.6612, -79.3750],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Ryerson / TMU Campus",
        "type": "landmark",
        "region": "Downtown Yonge / Church-Wellesley",
        "position": [43.6577, -79.3790],
        "metadata_": {"category": "education", "address": "350 Victoria St"},
    },

    # -----------------------------------------------------------------------
    # Queen West / Trinity-Bellwoods neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Trinity Bellwoods Park",
        "type": "landmark",
        "region": "Queen West / Trinity-Bellwoods",
        "position": [43.6472, -79.4135],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Queen West Art Crawl",
        "type": "building",
        "region": "Queen West / Trinity-Bellwoods",
        "position": [43.6475, -79.4050],
        "metadata_": {"category": "retail"},
    },
    {
        "name": "Ossington Strip",
        "type": "building",
        "region": "Queen West / Trinity-Bellwoods",
        "position": [43.6488, -79.4200],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # Liberty Village / Exhibition neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Liberty Village",
        "type": "neighborhood",
        "region": "Liberty Village / Exhibition",
        "position": [43.6382, -79.4209],
        "metadata_": {"description": "Trendy tech and creative industry hub"},
    },
    {
        "name": "Liberty Village Office Campus",
        "type": "building",
        "region": "Liberty Village / Exhibition",
        "position": [43.6388, -79.4198],
        "metadata_": {"category": "office"},
    },
    {
        "name": "Ernest Thompson Park",
        "type": "landmark",
        "region": "Liberty Village / Exhibition",
        "position": [43.6375, -79.4220],
        "metadata_": {"category": "park"},
    },
    {
        "name": "F45 Training Liberty Village",
        "type": "building",
        "region": "Liberty Village / Exhibition",
        "position": [43.6380, -79.4205],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "The Brazen Head Liberty Village",
        "type": "building",
        "region": "Liberty Village / Exhibition",
        "position": [43.6392, -79.4215],
        "metadata_": {"category": "restaurant"},
    },
    {
        "name": "Liberty Market Building",
        "type": "building",
        "region": "Liberty Village / Exhibition",
        "position": [43.6371, -79.4218],
        "metadata_": {"category": "office", "address": "171 East Liberty St"},
    },

    # -----------------------------------------------------------------------
    # Government District (work district)
    # -----------------------------------------------------------------------
    {
        "name": "Queen's Park",
        "type": "district",
        "region": "Government District",
        "position": [43.6600, -79.3922],
        "metadata_": {"description": "Provincial government and legislative district"},
    },
    {
        "name": "Ontario Legislative Assembly",
        "type": "landmark",
        "region": "Government District",
        "position": [43.6627, -79.3929],
        "metadata_": {"category": "government", "address": "Queen's Park"},
    },
    {
        "name": "Queen's Park Green",
        "type": "landmark",
        "region": "Government District",
        "position": [43.6614, -79.3920],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Ontario Government Offices",
        "type": "building",
        "region": "Government District",
        "position": [43.6590, -79.3885],
        "metadata_": {"category": "government", "address": "900 Bay St"},
    },
    {
        "name": "Ministry of Finance Building",
        "type": "building",
        "region": "Government District",
        "position": [43.6581, -79.3897],
        "metadata_": {"category": "government", "address": "Frost Building"},
    },
    {
        "name": "Queen's Park Café",
        "type": "building",
        "region": "Government District",
        "position": [43.6605, -79.3935],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # UofT District (work district)
    # -----------------------------------------------------------------------
    {
        "name": "University District",
        "type": "district",
        "region": "UofT District",
        "position": [43.6629, -79.3957],
        "metadata_": {"description": "Post-secondary education corridor"},
    },
    {
        "name": "University of Toronto - St. George Campus",
        "type": "landmark",
        "region": "UofT District",
        "position": [43.6629, -79.3957],
        "metadata_": {"category": "education", "address": "27 King's College Cir"},
    },
    {
        "name": "Hart House",
        "type": "landmark",
        "region": "UofT District",
        "position": [43.6648, -79.3961],
        "metadata_": {"category": "education", "address": "7 Hart House Cir"},
    },
    {
        "name": "Robarts Library",
        "type": "landmark",
        "region": "UofT District",
        "position": [43.6645, -79.3992],
        "metadata_": {"category": "education", "address": "130 St George St"},
    },
    {
        "name": "Athletic Centre UofT",
        "type": "building",
        "region": "UofT District",
        "position": [43.6618, -79.3972],
        "metadata_": {"category": "gym", "address": "55 Harbord St"},
    },
    {
        "name": "Victoria College Dining Hall",
        "type": "building",
        "region": "UofT District",
        "position": [43.6657, -79.3930],
        "metadata_": {"category": "restaurant"},
    },
    {
        "name": "Bahen Centre for Information Technology",
        "type": "building",
        "region": "UofT District",
        "position": [43.6597, -79.3978],
        "metadata_": {"category": "education", "address": "40 St George St"},
    },

    # -----------------------------------------------------------------------
    # Hospital Row (work district)
    # -----------------------------------------------------------------------
    {
        "name": "University Health Network - Toronto General",
        "type": "landmark",
        "region": "Hospital Row",
        "position": [43.6591, -79.3877],
        "metadata_": {"category": "hospital", "address": "200 Elizabeth St"},
    },
    {
        "name": "Mount Sinai Hospital",
        "type": "landmark",
        "region": "Hospital Row",
        "position": [43.6573, -79.3905],
        "metadata_": {"category": "hospital", "address": "600 University Ave"},
    },
    {
        "name": "SickKids Hospital",
        "type": "landmark",
        "region": "Hospital Row",
        "position": [43.6568, -79.3877],
        "metadata_": {"category": "hospital", "address": "555 University Ave"},
    },
    {
        "name": "Princess Margaret Cancer Centre",
        "type": "landmark",
        "region": "Hospital Row",
        "position": [43.6583, -79.3865],
        "metadata_": {"category": "hospital", "address": "610 University Ave"},
    },

    # -----------------------------------------------------------------------
    # TMU District (work district)
    # -----------------------------------------------------------------------
    {
        "name": "TMU Student Learning Centre",
        "type": "landmark",
        "region": "TMU District",
        "position": [43.6579, -79.3790],
        "metadata_": {"category": "education", "address": "341 Yonge St"},
    },
    {
        "name": "Yonge-Dundas Square",
        "type": "landmark",
        "region": "TMU District",
        "position": [43.6561, -79.3803],
        "metadata_": {"category": "retail", "address": "1 Dundas St E"},
    },
    {
        "name": "TMU Image Arts Centre",
        "type": "building",
        "region": "TMU District",
        "position": [43.6588, -79.3795],
        "metadata_": {"category": "education", "address": "122 Bond St"},
    },

    # -----------------------------------------------------------------------
    # Tech Corridor (work district)
    # -----------------------------------------------------------------------
    {
        "name": "MaRS Discovery District",
        "type": "landmark",
        "region": "Tech Corridor",
        "position": [43.6601, -79.3903],
        "metadata_": {"category": "office", "address": "101 College St"},
    },

    # -----------------------------------------------------------------------
    # CNE / Exhibition Place (work district)
    # -----------------------------------------------------------------------
    {
        "name": "Exhibition Place",
        "type": "landmark",
        "region": "CNE / Exhibition Place",
        "position": [43.6363, -79.4186],
        "metadata_": {"category": "event_venue", "address": "Exhibition Place"},
    },
    {
        "name": "BMO Field",
        "type": "landmark",
        "region": "CNE / Exhibition Place",
        "position": [43.6332, -79.4186],
        "metadata_": {"category": "stadium", "address": "170 Princes' Blvd"},
    },
    {
        "name": "Enercare Centre",
        "type": "building",
        "region": "CNE / Exhibition Place",
        "position": [43.6342, -79.4145],
        "metadata_": {"category": "event_venue", "address": "100 Princes' Blvd"},
    },

    # -----------------------------------------------------------------------
    # Corktown / Distillery neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Distillery District",
        "type": "landmark",
        "region": "Corktown / Distillery",
        "position": [43.6503, -79.3595],
        "metadata_": {"category": "retail", "address": "55 Mill St"},
    },
    {
        "name": "Corktown Common",
        "type": "landmark",
        "region": "Corktown / Distillery",
        "position": [43.6525, -79.3540],
        "metadata_": {"category": "park"},
    },

    # -----------------------------------------------------------------------
    # Cabbagetown / Regent Park neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Riverdale Park",
        "type": "landmark",
        "region": "Cabbagetown / Regent Park",
        "position": [43.6680, -79.3595],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Regent Park Community Centre",
        "type": "building",
        "region": "Cabbagetown / Regent Park",
        "position": [43.6590, -79.3600],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "Cabbagetown Heritage Houses",
        "type": "building",
        "region": "Cabbagetown / Regent Park",
        "position": [43.6650, -79.3620],
        "metadata_": {"category": "residential"},
    },

    # -----------------------------------------------------------------------
    # Entertainment / Harbourfront neighbourhood
    # -----------------------------------------------------------------------
    {
        "name": "Harbourfront Centre",
        "type": "landmark",
        "region": "Entertainment / Harbourfront",
        "position": [43.6387, -79.3806],
        "metadata_": {"category": "park", "address": "235 Queens Quay W"},
    },
    {
        "name": "Toronto Islands Ferry Terminal",
        "type": "landmark",
        "region": "Entertainment / Harbourfront",
        "position": [43.6415, -79.3762],
        "metadata_": {"category": "transit", "address": "9 Queens Quay W"},
    },
    {
        "name": "CN Tower",
        "type": "landmark",
        "region": "Entertainment / Harbourfront",
        "position": [43.6426, -79.3871],
        "metadata_": {"category": "landmark", "address": "290 Bremner Blvd"},
    },

    # -----------------------------------------------------------------------
    # Financial / St. Lawrence neighbourhood (more locations)
    # -----------------------------------------------------------------------
    {
        "name": "St. Lawrence Market",
        "type": "landmark",
        "region": "Financial / St. Lawrence",
        "position": [43.6489, -79.3715],
        "metadata_": {"category": "retail", "address": "93 Front St E"},
    },
    {
        "name": "Union Station",
        "type": "landmark",
        "region": "Financial / St. Lawrence",
        "position": [43.6453, -79.3806],
        "metadata_": {"category": "transit", "address": "65 Front St W"},
    },
    {
        "name": "Sugar Beach",
        "type": "landmark",
        "region": "Financial / St. Lawrence",
        "position": [43.6428, -79.3682],
        "metadata_": {"category": "park"},
    },
]
