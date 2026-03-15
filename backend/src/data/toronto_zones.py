"""
Toronto zone definitions for Agentropolis: residential neighborhoods and work districts.

Residential neighborhoods tile 100% of the viewable map area using Voronoi cells
computed from seed points, clipped to a land polygon that follows the Toronto
shoreline. Work districts are focused employment clusters.

Voronoi cells produce organic, natural-looking boundaries that:
- Cover 100% of visible land with no gaps
- Follow the shoreline (0% water overlap)
- Extend well beyond maxBounds to cover the full viewport at minZoom
"""

from __future__ import annotations

import logging
from typing import Any

from shapely.geometry import MultiPoint, Point, Polygon, box, mapping
from shapely.ops import voronoi_diagram

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Land polygon: extended clip boundary + Toronto shoreline
# ---------------------------------------------------------------------------
# Covers full visible viewport at minZoom 13 (well beyond maxBounds).
# Southern edge follows the approximate Lake Ontario / Toronto Harbour shoreline.

LAND_POLYGON = Polygon([
    # Top edge (west to east)
    (-79.46, 43.71), (-79.30, 43.71),
    # East edge down to shoreline
    (-79.30, 43.648),
    # Shoreline waypoints (east to west)
    (-79.330, 43.646),   # Cherry Beach approach
    (-79.340, 43.644),   # Keating Channel / Villiers Island
    (-79.350, 43.641),   # Sugar Beach / Sherbourne Common
    (-79.363, 43.639),   # Jarvis slip
    (-79.373, 43.638),   # Yonge Quay / Jack Layton Ferry Terminal
    (-79.383, 43.637),   # York Quay / Harbourfront Centre
    (-79.395, 43.636),   # Spadina Quay / HTO Park
    (-79.405, 43.634),   # Bathurst Quay
    (-79.420, 43.635),   # CNE shoreline
    (-79.46, 43.633),    # Exhibition / Ontario Place waterfront
    # Close
    (-79.46, 43.71),
])

# ---------------------------------------------------------------------------
# Seed points — one per zone, used to generate Voronoi cells
# ---------------------------------------------------------------------------

RESIDENTIAL_SEEDS: dict[str, tuple[float, float]] = {
    "Liberty Village / Exhibition":      (-79.411, 43.640),
    "Queen West / Trinity-Bellwoods":    (-79.416, 43.670),
    "Entertainment / Harbourfront":      (-79.390, 43.643),
    "Chinatown / Kensington":            (-79.392, 43.668),
    "Financial / St. Lawrence":          (-79.373, 43.645),
    "Downtown Yonge / Church-Wellesley": (-79.373, 43.668),
    "Corktown / Distillery":             (-79.348, 43.650),
    "Cabbagetown / Regent Park":         (-79.348, 43.670),
}

WORK_DISTRICT_SEEDS: dict[str, tuple[float, float]] = {
    "Financial District":    (-79.3805, 43.6485),
    "Entertainment District":(-79.393, 43.6465),
    "Tech Corridor":         (-79.4125, 43.6405),
    "UofT District":         (-79.3945, 43.6635),
    "TMU District":          (-79.380, 43.659),
    "Government District":   (-79.3895, 43.659),
    "Hospital Row":          (-79.388, 43.6615),
    "CNE / Exhibition Place":(-79.4125, 43.636),
}

# Original work district rectangular bounds (from main).
# Used as local clip envelopes so Voronoi cells don't expand beyond their area.
# Format: (min_lng, min_lat, max_lng, max_lat)
_WORK_DISTRICT_BOUNDS: dict[str, tuple[float, float, float, float]] = {
    "Financial District":     (-79.387, 43.644, -79.374, 43.653),
    "Entertainment District": (-79.400, 43.642, -79.386, 43.651),
    "Tech Corridor":          (-79.420, 43.636, -79.405, 43.645),
    "UofT District":          (-79.401, 43.658, -79.388, 43.669),
    "TMU District":           (-79.385, 43.654, -79.375, 43.664),
    "Government District":    (-79.396, 43.652, -79.383, 43.666),
    "Hospital Row":           (-79.393, 43.655, -79.383, 43.668),
    "CNE / Exhibition Place": (-79.420, 43.633, -79.405, 43.639),
}
_WORK_BUFFER = 0.003  # ~300m buffer around original bounds

# ---------------------------------------------------------------------------
# Zone metadata (colors + descriptions, keyed by name)
# ---------------------------------------------------------------------------

_RESIDENTIAL_META: dict[str, dict[str, str]] = {
    "Liberty Village / Exhibition": {
        "color": "#10b981",
        "description": "Liberty Village, CNE, Fort York, CityPlace",
    },
    "Queen West / Trinity-Bellwoods": {
        "color": "#f59e0b",
        "description": "Queen West, Ossington, Trinity-Bellwoods, Little Portugal",
    },
    "Entertainment / Harbourfront": {
        "color": "#3b82f6",
        "description": "Entertainment District, Harbourfront Centre, Rogers Centre",
    },
    "Chinatown / Kensington": {
        "color": "#ef4444",
        "description": "Kensington Market, Chinatown, U of T, Annex, Baldwin Village",
    },
    "Financial / St. Lawrence": {
        "color": "#22c55e",
        "description": "Bay Street, Union Station, St. Lawrence Market, PATH",
    },
    "Downtown Yonge / Church-Wellesley": {
        "color": "#a855f7",
        "description": "Dundas Square, Church-Wellesley Village, TMU area, Allan Gardens",
    },
    "Corktown / Distillery": {
        "color": "#f97316",
        "description": "Distillery District, Corktown, West Don Lands, lower Regent Park",
    },
    "Cabbagetown / Regent Park": {
        "color": "#06b6d4",
        "description": "Cabbagetown, upper Regent Park, Riverdale, north of Carlton",
    },
}

_WORK_DISTRICT_META: dict[str, dict[str, str]] = {
    "Financial District": {
        "color": "#2563eb",
        "description": "Bay Street banks, TD/BMO/RBC/Scotia towers, PATH",
    },
    "Entertainment District": {
        "color": "#7c3aed",
        "description": "King West, theatres, Rogers Centre, Scotiabank Arena",
    },
    "Tech Corridor": {
        "color": "#0891b2",
        "description": "Liberty Village tech offices, startup lofts",
    },
    "UofT District": {
        "color": "#1d4ed8",
        "description": "U of T St. George campus, Robarts, Hart House, Bahen",
    },
    "TMU District": {
        "color": "#0369a1",
        "description": "TMU campus, Yonge-Dundas Square, Student Learning Centre",
    },
    "Government District": {
        "color": "#b91c1c",
        "description": "Queen's Park, City Hall, Ontario Legislature, ministries",
    },
    "Hospital Row": {
        "color": "#dc2626",
        "description": "UHN Toronto General, SickKids, Mount Sinai, Princess Margaret",
    },
    "CNE / Exhibition Place": {
        "color": "#ca8a04",
        "description": "Exhibition Place, Enercare Centre, BMO Field, Ontario Place",
    },
}

# ---------------------------------------------------------------------------
# Voronoi computation (runs once at module load, cached)
# ---------------------------------------------------------------------------


def _compute_voronoi_cells(
    seeds: dict[str, tuple[float, float]],
    clip_polygon: Polygon,
) -> dict[str, Polygon]:
    """Compute Voronoi cells from seed points, clipped to land polygon."""
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


def _compute_work_district_cells(
    seeds: dict[str, tuple[float, float]],
    clip_polygon: Polygon,
) -> dict[str, Polygon]:
    """Compute Voronoi cells for work districts, clipped to local envelopes.

    Each cell is intersected with both the land polygon (shoreline) and a
    buffered version of the district's original rectangular bounds, so
    districts get organic Voronoi edges where they neighbor each other
    but don't expand beyond their intended area.
    """
    points = MultiPoint([Point(lng, lat) for lng, lat in seeds.values()])
    regions = voronoi_diagram(points, envelope=clip_polygon)

    cells: dict[str, Polygon] = {}
    for name, (lng, lat) in seeds.items():
        seed_pt = Point(lng, lat)
        for cell in regions.geoms:
            if cell.contains(seed_pt):
                clipped = cell.intersection(clip_polygon)
                # Clip to local envelope (buffered original bounds)
                ob = _WORK_DISTRICT_BOUNDS[name]
                local_env = box(
                    ob[0] - _WORK_BUFFER, ob[1] - _WORK_BUFFER,
                    ob[2] + _WORK_BUFFER, ob[3] + _WORK_BUFFER,
                )
                clipped = clipped.intersection(local_env)
                cells[name] = clipped
                break
    return cells


RESIDENTIAL_CELLS = _compute_voronoi_cells(RESIDENTIAL_SEEDS, LAND_POLYGON)
WORK_DISTRICT_CELLS = _compute_work_district_cells(WORK_DISTRICT_SEEDS, LAND_POLYGON)

# ---------------------------------------------------------------------------
# Build RESIDENTIAL_NEIGHBORHOODS / WORK_DISTRICTS dicts (backward compat)
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

# Merged cell lookup for point-in-polygon checks
ALL_CELLS: dict[str, Polygon] = {**RESIDENTIAL_CELLS, **WORK_DISTRICT_CELLS}

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
                "color": meta[name]["color"],
                "description": meta[name]["description"],
            },
            "geometry": mapping(cell),
        })
    return {"type": "FeatureCollection", "features": features}


def get_residential_geojson() -> dict:
    return _cells_to_geojson(RESIDENTIAL_CELLS, _RESIDENTIAL_META)


def get_work_district_geojson() -> dict:
    return _cells_to_geojson(WORK_DISTRICT_CELLS, _WORK_DISTRICT_META)
