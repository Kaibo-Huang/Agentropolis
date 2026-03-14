"""
Toronto zone definitions for Agentropolis: residential neighborhoods and work districts.

Residential neighborhoods tile 100% of the viewable map area (no gaps, no water overlap).
Work districts are focused employment clusters within the viewable area.

Map viewable bounds: [-79.42, 43.62] to [-79.32, 43.69]
Lake Ontario shoreline: approx 43.636 (west) to 43.641 (east)

Grid layout for residential neighborhoods:
  4 columns (dividers: Spadina -79.397, Yonge -79.383, Parliament -79.363)
  x 2 rows (divider: Queen St 43.652)
  Southern edges follow the approximate shoreline.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Residential neighborhoods (8) — 100% tiling of viewable land
# ---------------------------------------------------------------------------

RESIDENTIAL_NEIGHBORHOODS: dict[str, dict] = {
    "Liberty Village / Exhibition": {
        "bounds": {
            "min_lat": 43.636,
            "max_lat": 43.652,
            "min_lng": -79.420,
            "max_lng": -79.397,
        },
        # Polygon follows approximate shoreline on south edge
        "polygon": [
            [-79.420, 43.636],
            [-79.408, 43.635],
            [-79.397, 43.636],
            [-79.397, 43.652],
            [-79.420, 43.652],
            [-79.420, 43.636],
        ],
        "color": "#10b981",  # emerald
        "description": "Liberty Village, CNE, Fort York, CityPlace",
    },
    "Queen West / Trinity-Bellwoods": {
        "bounds": {
            "min_lat": 43.652,
            "max_lat": 43.690,
            "min_lng": -79.420,
            "max_lng": -79.397,
        },
        "polygon": [
            [-79.420, 43.652],
            [-79.397, 43.652],
            [-79.397, 43.690],
            [-79.420, 43.690],
            [-79.420, 43.652],
        ],
        "color": "#f59e0b",  # amber
        "description": "Queen West, Ossington, Trinity-Bellwoods, Little Portugal",
    },
    "Entertainment / Harbourfront": {
        "bounds": {
            "min_lat": 43.637,
            "max_lat": 43.652,
            "min_lng": -79.397,
            "max_lng": -79.383,
        },
        "polygon": [
            [-79.397, 43.637],
            [-79.390, 43.636],
            [-79.383, 43.637],
            [-79.383, 43.652],
            [-79.397, 43.652],
            [-79.397, 43.637],
        ],
        "color": "#3b82f6",  # blue
        "description": "Entertainment District, Harbourfront Centre, Rogers Centre",
    },
    "Chinatown / Kensington": {
        "bounds": {
            "min_lat": 43.652,
            "max_lat": 43.690,
            "min_lng": -79.397,
            "max_lng": -79.383,
        },
        "polygon": [
            [-79.397, 43.652],
            [-79.383, 43.652],
            [-79.383, 43.690],
            [-79.397, 43.690],
            [-79.397, 43.652],
        ],
        "color": "#ef4444",  # red
        "description": "Kensington Market, Chinatown, U of T, Annex, Baldwin Village",
    },
    "Financial / St. Lawrence": {
        "bounds": {
            "min_lat": 43.638,
            "max_lat": 43.652,
            "min_lng": -79.383,
            "max_lng": -79.363,
        },
        "polygon": [
            [-79.383, 43.638],
            [-79.375, 43.637],
            [-79.363, 43.638],
            [-79.363, 43.652],
            [-79.383, 43.652],
            [-79.383, 43.638],
        ],
        "color": "#22c55e",  # green
        "description": "Bay Street, Union Station, St. Lawrence Market, PATH",
    },
    "Downtown Yonge / Church-Wellesley": {
        "bounds": {
            "min_lat": 43.652,
            "max_lat": 43.690,
            "min_lng": -79.383,
            "max_lng": -79.363,
        },
        "polygon": [
            [-79.383, 43.652],
            [-79.363, 43.652],
            [-79.363, 43.690],
            [-79.383, 43.690],
            [-79.383, 43.652],
        ],
        "color": "#a855f7",  # purple
        "description": "Dundas Square, Church-Wellesley Village, TMU area, Allan Gardens",
    },
    "Corktown / Distillery": {
        "bounds": {
            "min_lat": 43.641,
            "max_lat": 43.652,
            "min_lng": -79.363,
            "max_lng": -79.320,
        },
        "polygon": [
            [-79.363, 43.641],
            [-79.350, 43.642],
            [-79.340, 43.644],
            [-79.320, 43.648],
            [-79.320, 43.652],
            [-79.363, 43.652],
            [-79.363, 43.641],
        ],
        "color": "#f97316",  # orange
        "description": "Distillery District, Corktown, West Don Lands, lower Regent Park",
    },
    "Cabbagetown / Regent Park": {
        "bounds": {
            "min_lat": 43.652,
            "max_lat": 43.690,
            "min_lng": -79.363,
            "max_lng": -79.320,
        },
        "polygon": [
            [-79.363, 43.652],
            [-79.320, 43.652],
            [-79.320, 43.690],
            [-79.363, 43.690],
            [-79.363, 43.652],
        ],
        "color": "#06b6d4",  # cyan
        "description": "Cabbagetown, upper Regent Park, Riverdale, north of Carlton",
    },
}

# ---------------------------------------------------------------------------
# Work districts (8) — focused employment clusters
# ---------------------------------------------------------------------------

WORK_DISTRICTS: dict[str, dict] = {
    "Financial District": {
        "bounds": {
            "min_lat": 43.644,
            "max_lat": 43.653,
            "min_lng": -79.387,
            "max_lng": -79.374,
        },
        "polygon": [
            [-79.387, 43.644],
            [-79.374, 43.644],
            [-79.374, 43.653],
            [-79.387, 43.653],
            [-79.387, 43.644],
        ],
        "color": "#2563eb",  # blue-600
        "description": "Bay Street banks, TD/BMO/RBC/Scotia towers, PATH",
    },
    "Entertainment District": {
        "bounds": {
            "min_lat": 43.642,
            "max_lat": 43.651,
            "min_lng": -79.400,
            "max_lng": -79.386,
        },
        "polygon": [
            [-79.400, 43.642],
            [-79.386, 43.642],
            [-79.386, 43.651],
            [-79.400, 43.651],
            [-79.400, 43.642],
        ],
        "color": "#7c3aed",  # violet-600
        "description": "King West, theatres, Rogers Centre, Scotiabank Arena",
    },
    "Tech Corridor": {
        "bounds": {
            "min_lat": 43.636,
            "max_lat": 43.645,
            "min_lng": -79.420,
            "max_lng": -79.405,
        },
        "polygon": [
            [-79.420, 43.636],
            [-79.405, 43.636],
            [-79.405, 43.645],
            [-79.420, 43.645],
            [-79.420, 43.636],
        ],
        "color": "#0891b2",  # cyan-600
        "description": "Liberty Village tech offices, startup lofts",
    },
    "UofT District": {
        "bounds": {
            "min_lat": 43.658,
            "max_lat": 43.669,
            "min_lng": -79.401,
            "max_lng": -79.388,
        },
        "polygon": [
            [-79.401, 43.658],
            [-79.388, 43.658],
            [-79.388, 43.669],
            [-79.401, 43.669],
            [-79.401, 43.658],
        ],
        "color": "#1d4ed8",  # blue-700
        "description": "U of T St. George campus, Robarts, Hart House, Bahen",
    },
    "TMU District": {
        "bounds": {
            "min_lat": 43.654,
            "max_lat": 43.664,
            "min_lng": -79.385,
            "max_lng": -79.375,
        },
        "polygon": [
            [-79.385, 43.654],
            [-79.375, 43.654],
            [-79.375, 43.664],
            [-79.385, 43.664],
            [-79.385, 43.654],
        ],
        "color": "#0369a1",  # sky-700
        "description": "TMU campus, Yonge-Dundas Square, Student Learning Centre",
    },
    "Government District": {
        "bounds": {
            "min_lat": 43.652,
            "max_lat": 43.666,
            "min_lng": -79.396,
            "max_lng": -79.383,
        },
        "polygon": [
            [-79.396, 43.652],
            [-79.383, 43.652],
            [-79.383, 43.666],
            [-79.396, 43.666],
            [-79.396, 43.652],
        ],
        "color": "#b91c1c",  # red-700
        "description": "Queen's Park, City Hall, Ontario Legislature, ministries",
    },
    "Hospital Row": {
        "bounds": {
            "min_lat": 43.655,
            "max_lat": 43.668,
            "min_lng": -79.393,
            "max_lng": -79.383,
        },
        "polygon": [
            [-79.393, 43.655],
            [-79.383, 43.655],
            [-79.383, 43.668],
            [-79.393, 43.668],
            [-79.393, 43.655],
        ],
        "color": "#dc2626",  # red-500
        "description": "UHN Toronto General, SickKids, Mount Sinai, Princess Margaret",
    },
    "CNE / Exhibition Place": {
        "bounds": {
            "min_lat": 43.632,
            "max_lat": 43.639,
            "min_lng": -79.420,
            "max_lng": -79.405,
        },
        "polygon": [
            [-79.420, 43.633],
            [-79.405, 43.633],
            [-79.405, 43.639],
            [-79.420, 43.639],
            [-79.420, 43.633],
        ],
        "color": "#ca8a04",  # yellow-600
        "description": "Exhibition Place, Enercare Centre, BMO Field, Ontario Place",
    },
}

# ---------------------------------------------------------------------------
# Merged lookup for _random_position() — all zone bounds in one dict
# ---------------------------------------------------------------------------

ALL_ZONE_BOUNDS: dict[str, dict[str, float]] = {}
for _name, _zone in RESIDENTIAL_NEIGHBORHOODS.items():
    ALL_ZONE_BOUNDS[_name] = _zone["bounds"]
for _name, _zone in WORK_DISTRICTS.items():
    ALL_ZONE_BOUNDS[_name] = _zone["bounds"]

# ---------------------------------------------------------------------------
# Neighborhood name lists (convenience)
# ---------------------------------------------------------------------------

NEIGHBORHOOD_NAMES: list[str] = list(RESIDENTIAL_NEIGHBORHOODS.keys())
WORK_DISTRICT_NAMES: list[str] = list(WORK_DISTRICTS.keys())

# ---------------------------------------------------------------------------
# Fallback position (Downtown Core center)
# ---------------------------------------------------------------------------

_FALLBACK_POSITION: list[float] = [43.6510, -79.3832]

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_position_in_bounds(
    pos: list[float],
    bounds: dict[str, float],
) -> bool:
    """Check that a [lat, lng] falls within a bounding box.

    Parameters
    ----------
    pos : list[float]
        [latitude, longitude]
    bounds : dict
        Must have min_lat, max_lat, min_lng, max_lng keys.

    Returns
    -------
    bool
    """
    if len(pos) < 2:
        return False
    lat, lng = pos[0], pos[1]
    return (
        bounds["min_lat"] <= lat <= bounds["max_lat"]
        and bounds["min_lng"] <= lng <= bounds["max_lng"]
    )


def validate_position_in_zone(pos: list[float], zone_name: str) -> bool:
    """Check that a [lat, lng] falls within the named zone's bounding box."""
    bounds = ALL_ZONE_BOUNDS.get(zone_name)
    if bounds is None:
        logger.warning("Zone %r not found in ALL_ZONE_BOUNDS", zone_name)
        return False
    return validate_position_in_bounds(pos, bounds)


def get_zone_bounds(zone_name: str) -> dict[str, float] | None:
    """Return bounding box for a zone, or None if not found."""
    return ALL_ZONE_BOUNDS.get(zone_name)
