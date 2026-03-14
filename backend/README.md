# Agentropolis Backend

A FastAPI-powered simulation engine that runs AI-driven social agents in a virtual Toronto. Each agent (follower) belongs to a demographic archetype, makes autonomous decisions via LLM calls, and broadcasts updates over WebSocket.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [Neon](https://neon.tech/) PostgreSQL database
- An OpenAI API key

## Setup

### 1. Install dependencies

```bash
cd backend
uv pip install -e .
# or
pip install -e .
```

### 2. Configure environment variables

Create a `.env` file in the **project root** (`genai-genesis/.env`):

```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
OPENAI_API_KEY=sk-...
NEON_DB=postgresql://user:password@host/dbname?sslmode=require
YOUR_NEON_API_KEY=napi_...
```

### 3. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 4. Start the server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs are available at:

- **Swagger UI** &mdash; http://localhost:8000/docs
- **ReDoc** &mdash; http://localhost:8000/redoc
- **Health check** &mdash; `GET /health` returns `{"status": "ok"}`

## API Endpoints

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions` | Create a new simulation session |
| GET | `/api/sessions/{session_id}` | Get session state |
| DELETE | `/api/sessions/{session_id}` | Delete session (cascades all data) |
| POST | `/api/sessions/{session_id}/resume` | Start / resume the simulation |
| POST | `/api/sessions/{session_id}/pause` | Pause the simulation |

### Simulation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions/{session_id}/tick` | Advance virtual time and run a tick |

### Events

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions/{session_id}/events` | Inject a narrative event into the simulation |

### Data

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sessions/{session_id}/archetypes` | List archetypes with follower counts |
| GET | `/api/sessions/{session_id}/followers` | List followers (paginated, default 50/page) |
| GET | `/api/sessions/{session_id}/posts` | List posts (paginated, default 50/page) |

### WebSocket

| Path | Description |
|------|-------------|
| `ws://localhost:8000/ws/{session_id}` | Real-time simulation updates |

## Typical Workflow

```
1. POST /api/sessions              → creates session, seeds archetypes/followers/companies
2. POST /api/sessions/{id}/resume  → sets status to "running"
3. POST /api/sessions/{id}/tick    → advances time, agents make decisions, posts generated
4. GET  /api/sessions/{id}/posts   → read what the agents produced
5. POST /api/sessions/{id}/events  → inject an event (e.g. "transit strike")
6. POST /api/sessions/{id}/tick    → agents react to the event
7. POST /api/sessions/{id}/pause   → pause when done
```

## Architecture

```
src/
├── main.py                  # FastAPI app, lifespan hooks
├── config.py                # Pydantic settings (reads .env)
├── api/                     # REST endpoints
├── ws/                      # WebSocket handler & connection manager
├── db/
│   ├── engine.py            # Async SQLAlchemy engine (asyncpg)
│   ├── models.py            # ORM models (sessions, archetypes, followers, ...)
│   └── queries.py           # Reusable query functions
├── agents/
│   ├── archetype_agent.py   # Tier 1 — one LLM call per archetype (gpt-4.1)
│   ├── follower_variation.py# Tier 2 — per-follower personalization (gpt-4.1-mini)
│   ├── tools.py             # Agent tools (events, memories, locations, etc.)
│   ├── schemas.py           # Pydantic output schemas for LLM responses
│   └── fallback.py          # Deterministic fallback when LLM fails
├── simulation/
│   ├── tick_orchestrator.py # Runs all archetypes in parallel (semaphore-bounded)
│   ├── health_tick.py       # Daily health metric updates
│   └── seeder.py            # Generates initial population on session create
└── data/                    # Static Toronto demographic/geographic data
```

### How a tick works

1. The client calls the **tick** endpoint with a target time.
2. The **tick orchestrator** fans out to all archetypes concurrently (max 5 in parallel).
3. Each **archetype agent** (Tier 1) calls an LLM with context about events, memories, and nearby locations to decide what its followers should do.
4. Each **follower variation agent** (Tier 2) personalizes the archetype's plan per follower &mdash; adjusting happiness, timing, and generating tweets.
5. Results are persisted (memories, posts, stat updates) and broadcast via WebSocket.
6. If the LLM fails after 3 retries, a deterministic **fallback** keeps the simulation running.
