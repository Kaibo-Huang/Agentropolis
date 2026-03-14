"""
Toronto neighborhood static data for the Agentropolis Location table.

TORONTO_NEIGHBORHOODS: list of dicts matching the Location model schema
    (name, type, region, position, metadata_)

NEIGHBORHOOD_BOUNDS: dict keyed by region name with bounding box values
    used for random position jitter when generating follower/company positions.
    Each entry: {"min_lat": float, "max_lat": float, "min_lng": float, "max_lng": float}
"""

# ---------------------------------------------------------------------------
# Bounding boxes (min_lat, max_lat, min_lng, max_lng) per region
# Used by the seeder to generate positions within a region.
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
# ---------------------------------------------------------------------------

TORONTO_NEIGHBORHOODS: list[dict] = [
    # -----------------------------------------------------------------------
    # Downtown Core
    # -----------------------------------------------------------------------
    {
        "name": "Downtown Core",
        "type": "neighborhood",
        "region": "Downtown Core",
        "position": [43.6510, -79.3832],
        "metadata_": {"description": "The central business and cultural hub of Toronto"},
    },
    {
        "name": "City Hall",
        "type": "landmark",
        "region": "Downtown Core",
        "position": [43.6534, -79.3839],
        "metadata_": {"category": "government", "address": "100 Queen St W"},
    },
    {
        "name": "Eaton Centre",
        "type": "landmark",
        "region": "Downtown Core",
        "position": [43.6544, -79.3807],
        "metadata_": {"category": "retail", "address": "220 Yonge St"},
    },
    {
        "name": "Nathan Phillips Square",
        "type": "landmark",
        "region": "Downtown Core",
        "position": [43.6528, -79.3842],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Downtown Core Community Centre",
        "type": "building",
        "region": "Downtown Core",
        "position": [43.6490, -79.3820],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "St. Patrick's Market",
        "type": "building",
        "region": "Downtown Core",
        "position": [43.6515, -79.3855],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # Financial District
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
    # Entertainment District
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
    # Midtown
    # -----------------------------------------------------------------------
    {
        "name": "Midtown",
        "type": "neighborhood",
        "region": "Midtown",
        "position": [43.6988, -79.3934],
        "metadata_": {"description": "Residential and commercial midtown corridor"},
    },
    {
        "name": "Mount Sinai Hospital",
        "type": "landmark",
        "region": "Midtown",
        "position": [43.6573, -79.3905],
        "metadata_": {"category": "hospital", "address": "600 University Ave"},
    },
    {
        "name": "Women's College Hospital",
        "type": "landmark",
        "region": "Midtown",
        "position": [43.6623, -79.3933],
        "metadata_": {"category": "hospital", "address": "76 Grenville St"},
    },
    {
        "name": "Yonge & Eglinton Centre",
        "type": "landmark",
        "region": "Midtown",
        "position": [43.7071, -79.3986],
        "metadata_": {"category": "retail", "address": "2300 Yonge St"},
    },
    {
        "name": "Midtown Athletic Club",
        "type": "building",
        "region": "Midtown",
        "position": [43.7010, -79.3955],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "Davisville Park",
        "type": "landmark",
        "region": "Midtown",
        "position": [43.7003, -79.3882],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Midtown Café",
        "type": "building",
        "region": "Midtown",
        "position": [43.6990, -79.3940],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # North York
    # -----------------------------------------------------------------------
    {
        "name": "North York",
        "type": "neighborhood",
        "region": "North York",
        "position": [43.7615, -79.4111],
        "metadata_": {"description": "Major suburban centre north of downtown"},
    },
    {
        "name": "Mel Lastman Square",
        "type": "landmark",
        "region": "North York",
        "position": [43.7680, -79.4128],
        "metadata_": {"category": "park", "address": "5100 Yonge St"},
    },
    {
        "name": "North York Civic Centre",
        "type": "landmark",
        "region": "North York",
        "position": [43.7688, -79.4131],
        "metadata_": {"category": "government", "address": "5100 Yonge St"},
    },
    {
        "name": "Fairview Mall",
        "type": "landmark",
        "region": "North York",
        "position": [43.7793, -79.3440],
        "metadata_": {"category": "retail", "address": "1800 Sheppard Ave E"},
    },
    {
        "name": "North York General Hospital",
        "type": "landmark",
        "region": "North York",
        "position": [43.7608, -79.3889],
        "metadata_": {"category": "hospital", "address": "4001 Leslie St"},
    },
    {
        "name": "Earl Bales Park",
        "type": "landmark",
        "region": "North York",
        "position": [43.7617, -79.4377],
        "metadata_": {"category": "park"},
    },
    {
        "name": "North York Fitness Centre",
        "type": "building",
        "region": "North York",
        "position": [43.7620, -79.4115],
        "metadata_": {"category": "gym"},
    },

    # -----------------------------------------------------------------------
    # Scarborough
    # -----------------------------------------------------------------------
    {
        "name": "Scarborough",
        "type": "neighborhood",
        "region": "Scarborough",
        "position": [43.7731, -79.2578],
        "metadata_": {"description": "East Toronto's diverse suburban district"},
    },
    {
        "name": "Scarborough Town Centre",
        "type": "landmark",
        "region": "Scarborough",
        "position": [43.7750, -79.2577],
        "metadata_": {"category": "retail", "address": "300 Borough Dr"},
    },
    {
        "name": "Scarborough Civic Centre",
        "type": "landmark",
        "region": "Scarborough",
        "position": [43.7737, -79.2570],
        "metadata_": {"category": "government", "address": "150 Borough Dr"},
    },
    {
        "name": "Rouge National Urban Park",
        "type": "landmark",
        "region": "Scarborough",
        "position": [43.8082, -79.1723],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Scarborough Health Network",
        "type": "landmark",
        "region": "Scarborough",
        "position": [43.7626, -79.2369],
        "metadata_": {"category": "hospital", "address": "3050 Lawrence Ave E"},
    },
    {
        "name": "Scarborough Factory Lofts",
        "type": "building",
        "region": "Scarborough",
        "position": [43.7680, -79.2800],
        "metadata_": {"category": "manufacturing"},
    },
    {
        "name": "Scarborough Recreation Centre",
        "type": "building",
        "region": "Scarborough",
        "position": [43.7700, -79.2600],
        "metadata_": {"category": "gym"},
    },

    # -----------------------------------------------------------------------
    # Etobicoke
    # -----------------------------------------------------------------------
    {
        "name": "Etobicoke",
        "type": "neighborhood",
        "region": "Etobicoke",
        "position": [43.6205, -79.5132],
        "metadata_": {"description": "West Toronto borough with industrial and residential areas"},
    },
    {
        "name": "Sherway Gardens",
        "type": "landmark",
        "region": "Etobicoke",
        "position": [43.6098, -79.5545],
        "metadata_": {"category": "retail", "address": "25 The West Mall"},
    },
    {
        "name": "Humber River Hospital",
        "type": "landmark",
        "region": "Etobicoke",
        "position": [43.7332, -79.5458],
        "metadata_": {"category": "hospital", "address": "1235 Wilson Ave"},
    },
    {
        "name": "Centennial Park",
        "type": "landmark",
        "region": "Etobicoke",
        "position": [43.6384, -79.5583],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Etobicoke Industrial Park",
        "type": "building",
        "region": "Etobicoke",
        "position": [43.6220, -79.5150],
        "metadata_": {"category": "manufacturing"},
    },
    {
        "name": "Etobicoke Olympium",
        "type": "building",
        "region": "Etobicoke",
        "position": [43.6370, -79.5380],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "The Kingsway Restaurant Row",
        "type": "building",
        "region": "Etobicoke",
        "position": [43.6502, -79.5070],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # Waterfront
    # -----------------------------------------------------------------------
    {
        "name": "Waterfront",
        "type": "neighborhood",
        "region": "Waterfront",
        "position": [43.6390, -79.3812],
        "metadata_": {"description": "Toronto's Lake Ontario waterfront district"},
    },
    {
        "name": "Harbourfront Centre",
        "type": "landmark",
        "region": "Waterfront",
        "position": [43.6387, -79.3806],
        "metadata_": {"category": "park", "address": "235 Queens Quay W"},
    },
    {
        "name": "Toronto Islands Ferry Terminal",
        "type": "landmark",
        "region": "Waterfront",
        "position": [43.6415, -79.3762],
        "metadata_": {"category": "transit", "address": "9 Queens Quay W"},
    },
    {
        "name": "Sugar Beach",
        "type": "landmark",
        "region": "Waterfront",
        "position": [43.6428, -79.3682],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Waterfront Café & Bar",
        "type": "building",
        "region": "Waterfront",
        "position": [43.6380, -79.3820],
        "metadata_": {"category": "restaurant"},
    },
    {
        "name": "Waterfront Fitness",
        "type": "building",
        "region": "Waterfront",
        "position": [43.6395, -79.3790],
        "metadata_": {"category": "gym"},
    },

    # -----------------------------------------------------------------------
    # Yorkville
    # -----------------------------------------------------------------------
    {
        "name": "Yorkville",
        "type": "neighborhood",
        "region": "Yorkville",
        "position": [43.6709, -79.3932],
        "metadata_": {"description": "Upscale shopping and dining district"},
    },
    {
        "name": "Bloor-Yorkville Shopping District",
        "type": "landmark",
        "region": "Yorkville",
        "position": [43.6716, -79.3930],
        "metadata_": {"category": "retail"},
    },
    {
        "name": "Royal Ontario Museum",
        "type": "landmark",
        "region": "Yorkville",
        "position": [43.6677, -79.3948],
        "metadata_": {"category": "museum", "address": "100 Queens Park"},
    },
    {
        "name": "Hazelton Lanes",
        "type": "building",
        "region": "Yorkville",
        "position": [43.6738, -79.3959],
        "metadata_": {"category": "retail", "address": "55 Avenue Rd"},
    },
    {
        "name": "Yorkville Village Spa & Fitness",
        "type": "building",
        "region": "Yorkville",
        "position": [43.6720, -79.3945],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "Sassafraz Restaurant",
        "type": "building",
        "region": "Yorkville",
        "position": [43.6729, -79.3962],
        "metadata_": {"category": "restaurant", "address": "100 Cumberland St"},
    },
    {
        "name": "Ramsden Park",
        "type": "landmark",
        "region": "Yorkville",
        "position": [43.6757, -79.3913],
        "metadata_": {"category": "park"},
    },

    # -----------------------------------------------------------------------
    # Liberty Village
    # -----------------------------------------------------------------------
    {
        "name": "Liberty Village",
        "type": "neighborhood",
        "region": "Liberty Village",
        "position": [43.6382, -79.4209],
        "metadata_": {"description": "Trendy tech and creative industry hub"},
    },
    {
        "name": "Liberty Village Office Campus",
        "type": "building",
        "region": "Liberty Village",
        "position": [43.6388, -79.4198],
        "metadata_": {"category": "office"},
    },
    {
        "name": "Ernest Thompson Park",
        "type": "landmark",
        "region": "Liberty Village",
        "position": [43.6375, -79.4220],
        "metadata_": {"category": "park"},
    },
    {
        "name": "F45 Training Liberty Village",
        "type": "building",
        "region": "Liberty Village",
        "position": [43.6380, -79.4205],
        "metadata_": {"category": "gym"},
    },
    {
        "name": "The Brazen Head Liberty Village",
        "type": "building",
        "region": "Liberty Village",
        "position": [43.6392, -79.4215],
        "metadata_": {"category": "restaurant"},
    },
    {
        "name": "Liberty Market Building",
        "type": "building",
        "region": "Liberty Village",
        "position": [43.6371, -79.4218],
        "metadata_": {"category": "office", "address": "171 East Liberty St"},
    },

    # -----------------------------------------------------------------------
    # Queen's Park
    # -----------------------------------------------------------------------
    {
        "name": "Queen's Park",
        "type": "district",
        "region": "Queen's Park",
        "position": [43.6600, -79.3922],
        "metadata_": {"description": "Provincial government and legislative district"},
    },
    {
        "name": "Ontario Legislative Assembly",
        "type": "landmark",
        "region": "Queen's Park",
        "position": [43.6627, -79.3929],
        "metadata_": {"category": "government", "address": "Queen's Park"},
    },
    {
        "name": "Queen's Park Green",
        "type": "landmark",
        "region": "Queen's Park",
        "position": [43.6614, -79.3920],
        "metadata_": {"category": "park"},
    },
    {
        "name": "Ontario Government Offices",
        "type": "building",
        "region": "Queen's Park",
        "position": [43.6590, -79.3885],
        "metadata_": {"category": "government", "address": "900 Bay St"},
    },
    {
        "name": "Ministry of Finance Building",
        "type": "building",
        "region": "Queen's Park",
        "position": [43.6581, -79.3897],
        "metadata_": {"category": "government", "address": "Frost Building"},
    },
    {
        "name": "Queen's Park Café",
        "type": "building",
        "region": "Queen's Park",
        "position": [43.6605, -79.3935],
        "metadata_": {"category": "restaurant"},
    },

    # -----------------------------------------------------------------------
    # University District
    # -----------------------------------------------------------------------
    {
        "name": "University District",
        "type": "district",
        "region": "University District",
        "position": [43.6629, -79.3957],
        "metadata_": {"description": "Post-secondary education corridor"},
    },
    {
        "name": "University of Toronto - St. George Campus",
        "type": "landmark",
        "region": "University District",
        "position": [43.6629, -79.3957],
        "metadata_": {"category": "education", "address": "27 King's College Cir"},
    },
    {
        "name": "Hart House",
        "type": "landmark",
        "region": "University District",
        "position": [43.6648, -79.3961],
        "metadata_": {"category": "education", "address": "7 Hart House Cir"},
    },
    {
        "name": "Robarts Library",
        "type": "landmark",
        "region": "University District",
        "position": [43.6645, -79.3992],
        "metadata_": {"category": "education", "address": "130 St George St"},
    },
    {
        "name": "University Health Network - Toronto General",
        "type": "landmark",
        "region": "University District",
        "position": [43.6591, -79.3877],
        "metadata_": {"category": "hospital", "address": "200 Elizabeth St"},
    },
    {
        "name": "Athletic Centre UofT",
        "type": "building",
        "region": "University District",
        "position": [43.6618, -79.3972],
        "metadata_": {"category": "gym", "address": "55 Harbord St"},
    },
    {
        "name": "Victoria College Dining Hall",
        "type": "building",
        "region": "University District",
        "position": [43.6657, -79.3930],
        "metadata_": {"category": "restaurant"},
    },
    {
        "name": "Bahen Centre for Information Technology",
        "type": "building",
        "region": "University District",
        "position": [43.6597, -79.3978],
        "metadata_": {"category": "education", "address": "40 St George St"},
    },
]
