"""
Toronto zone definitions for Agentropolis: unified residential + work district map.

All 16 zones (8 residential neighborhoods + 8 work districts) are computed from
a single Voronoi diagram, giving continuous coverage of the city with no gaps.
Each zone has a `type` ("residential" or "work") so the frontend can style them
differently.

Voronoi cells produce organic, natural-looking boundaries that:
- Cover 100% of visible land with no gaps
- Follow the shoreline (0% water overlap)
- Extend well beyond maxBounds to cover the full viewport at minZoom
"""

from __future__ import annotations

import logging
from typing import Any

from shapely.geometry import MultiPoint, Point, Polygon, mapping
from shapely.ops import voronoi_diagram

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Land polygon: extended clip boundary + Toronto shoreline
# ---------------------------------------------------------------------------
# Covers full visible viewport at minZoom 13 (well beyond maxBounds).
# Southern edge follows the approximate Lake Ontario / Toronto Harbour shoreline.

LAND_POLYGON = Polygon([
    # Top edge (west to east) — extended to cover full viewport at zoom 13
    (-79.55, 43.75), (-79.24, 43.75),
    # East edge down to shoreline
    (-79.24, 43.648),
    # Shoreline waypoints (east to west) — refined to track actual waterfront
    (-79.30, 43.650),    # East Bayfront / Port Lands
    (-79.330, 43.648),   # Cherry Beach approach
    (-79.340, 43.647),   # Keating Channel / Villiers Island
    (-79.350, 43.6465),  # Sugar Beach / Sherbourne Common
    (-79.358, 43.6455),  # Parliament slip
    (-79.363, 43.642),   # Jarvis slip
    (-79.368, 43.641),   # Jarvis / Queens Quay
    (-79.373, 43.640),   # Yonge Quay / Jack Layton Ferry Terminal
    (-79.378, 43.637),   # York / Simcoe slip
    (-79.383, 43.637),   # York Quay / Harbourfront Centre
    (-79.389, 43.636),   # Rees St slip
    (-79.395, 43.635),   # Spadina Quay / HTO Park
    (-79.398, 43.634),   # Music Garden
    (-79.402, 43.633),   # Bathurst Quay / Portland slip
    (-79.407, 43.632),   # Stadium Rd / Fort York approach
    (-79.412, 43.631),   # Ontario Place / Budweiser Stage
    (-79.418, 43.630),   # BMO Field / Exhibition Place south edge
    (-79.425, 43.631),   # Exhibition Place west / Marilyn Bell Park
    (-79.435, 43.631),   # Sunnyside area
    (-79.45, 43.630),    # Humber Bay east
    (-79.55, 43.628),    # far west (Humber Bay / Mimico)
    # Close
    (-79.55, 43.75),
])

# ---------------------------------------------------------------------------
# Seed points — all zones in a single dict, tagged by type
# ---------------------------------------------------------------------------

ZONE_SEEDS: dict[str, tuple[float, float]] = {
    # Residential neighborhoods
    "Liberty Village / Exhibition":      (-79.411, 43.640),
    "Queen West / Trinity-Bellwoods":    (-79.416, 43.670),
    "Entertainment / Harbourfront":      (-79.390, 43.643),
    "Chinatown / Kensington":            (-79.392, 43.668),
    "Financial / St. Lawrence":          (-79.373, 43.649),
    "Downtown Yonge / Church-Wellesley": (-79.373, 43.668),
    "Corktown / Distillery":             (-79.348, 43.654),
    "Cabbagetown / Regent Park":         (-79.348, 43.670),
    # Work districts
    "Financial District":    (-79.3805, 43.6485),
    "Entertainment District":(-79.393, 43.6465),
    "Tech Corridor":         (-79.4125, 43.6405),
    "UofT District":         (-79.3945, 43.6635),
    "TMU District":          (-79.380, 43.659),
    "Government District":   (-79.3895, 43.659),
    "Hospital Row":          (-79.388, 43.6615),
    "CNE / Exhibition Place":(-79.4125, 43.636),
}

# Backward-compat aliases so existing code can still reference separate dicts
RESIDENTIAL_SEEDS: dict[str, tuple[float, float]] = {
    k: v for k, v in ZONE_SEEDS.items() if k in {
        "Liberty Village / Exhibition", "Queen West / Trinity-Bellwoods",
        "Entertainment / Harbourfront", "Chinatown / Kensington",
        "Financial / St. Lawrence", "Downtown Yonge / Church-Wellesley",
        "Corktown / Distillery", "Cabbagetown / Regent Park",
    }
}
WORK_DISTRICT_SEEDS: dict[str, tuple[float, float]] = {
    k: v for k, v in ZONE_SEEDS.items() if k not in RESIDENTIAL_SEEDS
}

# ---------------------------------------------------------------------------
# Zone metadata (colors + descriptions + type, keyed by name)
# ---------------------------------------------------------------------------

_ZONE_META: dict[str, dict[str, str]] = {
    # Residential
    "Liberty Village / Exhibition": {
        "type": "residential",
        "color": "#10b981",
        "description": "Liberty Village, CNE, Fort York, CityPlace",
    },
    "Queen West / Trinity-Bellwoods": {
        "type": "residential",
        "color": "#f59e0b",
        "description": "Queen West, Ossington, Trinity-Bellwoods, Little Portugal",
    },
    "Entertainment / Harbourfront": {
        "type": "residential",
        "color": "#3b82f6",
        "description": "Entertainment District, Harbourfront Centre, Rogers Centre",
    },
    "Chinatown / Kensington": {
        "type": "residential",
        "color": "#ef4444",
        "description": "Kensington Market, Chinatown, U of T, Annex, Baldwin Village",
    },
    "Financial / St. Lawrence": {
        "type": "residential",
        "color": "#22c55e",
        "description": "Bay Street, Union Station, St. Lawrence Market, PATH",
    },
    "Downtown Yonge / Church-Wellesley": {
        "type": "residential",
        "color": "#a855f7",
        "description": "Dundas Square, Church-Wellesley Village, TMU area, Allan Gardens",
    },
    "Corktown / Distillery": {
        "type": "residential",
        "color": "#f97316",
        "description": "Distillery District, Corktown, West Don Lands, lower Regent Park",
    },
    "Cabbagetown / Regent Park": {
        "type": "residential",
        "color": "#06b6d4",
        "description": "Cabbagetown, upper Regent Park, Riverdale, north of Carlton",
    },
    # Work districts
    "Financial District": {
        "type": "work",
        "color": "#2563eb",
        "description": "Bay Street banks, TD/BMO/RBC/Scotia towers, PATH",
    },
    "Entertainment District": {
        "type": "work",
        "color": "#7c3aed",
        "description": "King West, theatres, Rogers Centre, Scotiabank Arena",
    },
    "Tech Corridor": {
        "type": "work",
        "color": "#0891b2",
        "description": "Liberty Village tech offices, startup lofts",
    },
    "UofT District": {
        "type": "work",
        "color": "#1d4ed8",
        "description": "U of T St. George campus, Robarts, Hart House, Bahen",
    },
    "TMU District": {
        "type": "work",
        "color": "#0369a1",
        "description": "TMU campus, Yonge-Dundas Square, Student Learning Centre",
    },
    "Government District": {
        "type": "work",
        "color": "#b91c1c",
        "description": "Queen's Park, City Hall, Ontario Legislature, ministries",
    },
    "Hospital Row": {
        "type": "work",
        "color": "#dc2626",
        "description": "UHN Toronto General, SickKids, Mount Sinai, Princess Margaret",
    },
    "CNE / Exhibition Place": {
        "type": "work",
        "color": "#ca8a04",
        "description": "Exhibition Place, Enercare Centre, BMO Field, Ontario Place",
    },
}

# Backward-compat aliases for code that references the old separate dicts
_RESIDENTIAL_META = {k: v for k, v in _ZONE_META.items() if v["type"] == "residential"}
_WORK_DISTRICT_META = {k: v for k, v in _ZONE_META.items() if v["type"] == "work"}

# ---------------------------------------------------------------------------
# Unified Voronoi computation (runs once at module load, cached)
# ---------------------------------------------------------------------------


def _compute_unified_voronoi(
    seeds: dict[str, tuple[float, float]],
    clip_polygon: Polygon,
) -> dict[str, Polygon]:
    """Compute Voronoi cells from ALL seed points, clipped to land polygon.

    All 16 seeds participate in one diagram, producing continuous coverage
    with no gaps. Work district zones are naturally small because their seeds
    are densely clustered downtown.
    """
    points = MultiPoint([Point(lng, lat) for lng, lat in seeds.values()])
    regions = voronoi_diagram(points, envelope=clip_polygon)

    cells: dict[str, Polygon] = {}
    for name, (lng, lat) in seeds.items():
        seed_pt = Point(lng, lat)
        for cell in regions.geoms:
            if cell.contains(seed_pt):
                clipped = cell.intersection(clip_polygon)
                cells[name] = clipped
                break
    return cells


ALL_CELLS = _compute_unified_voronoi(ZONE_SEEDS, LAND_POLYGON)

# Split into residential/work for backward compat
RESIDENTIAL_CELLS = {k: v for k, v in ALL_CELLS.items() if k in RESIDENTIAL_SEEDS}
WORK_DISTRICT_CELLS = {k: v for k, v in ALL_CELLS.items() if k in WORK_DISTRICT_SEEDS}

# ---------------------------------------------------------------------------
# Build zone dicts (backward compat)
# ---------------------------------------------------------------------------


def _cell_to_polygon_coords(cell: Polygon) -> list[list[float]]:
    """Convert a Shapely polygon to a list of [lng, lat] coordinates."""
    coords = list(cell.exterior.coords)
    return [[round(c[0], 6), round(c[1], 6)] for c in coords]


def _build_zone_dict(
    cells: dict[str, Polygon],
    meta: dict[str, dict[str, str]],
) -> dict[str, dict[str, Any]]:
    zones: dict[str, dict[str, Any]] = {}
    for name, cell in cells.items():
        b = cell.bounds  # (min_lng, min_lat, max_lng, max_lat)
        zones[name] = {
            "bounds": {
                "min_lat": round(b[1], 6),
                "max_lat": round(b[3], 6),
                "min_lng": round(b[0], 6),
                "max_lng": round(b[2], 6),
            },
            "polygon": _cell_to_polygon_coords(cell),
            "color": meta[name]["color"],
            "description": meta[name]["description"],
        }
    return zones


RESIDENTIAL_NEIGHBORHOODS: dict[str, dict] = _build_zone_dict(
    RESIDENTIAL_CELLS, _RESIDENTIAL_META
)
WORK_DISTRICTS: dict[str, dict] = _build_zone_dict(
    WORK_DISTRICT_CELLS, _WORK_DISTRICT_META
)

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
    """Check that a [lat, lng] falls within a bounding box."""
    if len(pos) < 2:
        return False
    lat, lng = pos[0], pos[1]
    return (
        bounds["min_lat"] <= lat <= bounds["max_lat"]
        and bounds["min_lng"] <= lng <= bounds["max_lng"]
    )


def validate_position_in_zone(pos: list[float], zone_name: str) -> bool:
    """Check that a [lat, lng] falls within the named zone's Voronoi cell."""
    cell = ALL_CELLS.get(zone_name)
    if cell is None:
        logger.warning("Zone %r not found in ALL_CELLS", zone_name)
        return False
    lat, lng = pos[0], pos[1]
    return cell.contains(Point(lng, lat))


def get_zone_bounds(zone_name: str) -> dict[str, float] | None:
    """Return bounding box for a zone, or None if not found."""
    return ALL_ZONE_BOUNDS.get(zone_name)


# ---------------------------------------------------------------------------
# GeoJSON export (for API / frontend consumption)
# ---------------------------------------------------------------------------


def _cells_to_geojson(
    cells: dict[str, Polygon],
    meta: dict[str, dict[str, str]],
) -> dict:
    features = []
    for name, cell in cells.items():
        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "type": meta[name]["type"],
                "color": meta[name]["color"],
                "description": meta[name]["description"],
            },
            "geometry": mapping(cell),
        })
    return {"type": "FeatureCollection", "features": features}


def get_zones_geojson() -> dict:
    """Return all 16 zones as a single GeoJSON FeatureCollection."""
    return _cells_to_geojson(ALL_CELLS, _ZONE_META)


def get_residential_geojson() -> dict:
    """Return residential zones only (backward compat)."""
    return _cells_to_geojson(RESIDENTIAL_CELLS, _ZONE_META)


def get_work_district_geojson() -> dict:
    """Return work district zones only (backward compat)."""
    return _cells_to_geojson(WORK_DISTRICT_CELLS, _ZONE_META)
