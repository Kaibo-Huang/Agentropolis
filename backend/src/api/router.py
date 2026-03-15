from fastapi import APIRouter

from src.api.archetypes import router as archetypes_router
from src.api.events import router as events_router
from src.api.followers import router as followers_router
from src.api.posts import router as posts_router
from src.api.sessions import router as sessions_router
from src.api.tick import router as tick_router
from src.api.zones import router as zones_router

api_router = APIRouter(prefix="/api")
api_router.include_router(sessions_router)
api_router.include_router(tick_router)
api_router.include_router(events_router)
api_router.include_router(followers_router)
api_router.include_router(posts_router)
api_router.include_router(archetypes_router)
api_router.include_router(zones_router)
