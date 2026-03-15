"""Zone GeoJSON endpoints — serves pre-computed Voronoi cell polygons."""

from fastapi import APIRouter

from src.data.toronto_zones import get_residential_geojson, get_work_district_geojson

router = APIRouter(tags=["zones"])


@router.get("/zones/residential")
async def get_residential_zones():
    return get_residential_geojson()


@router.get("/zones/work-districts")
async def get_work_district_zones():
    return get_work_district_geojson()
