from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.db.engine import close_db, init_db
from src.ws.handler import router as ws_router
from src.ws.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await manager.start_heartbeat()
    yield
    await manager.stop_heartbeat()
    await close_db()


app = FastAPI(
    title="Agentropolis Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
