# Agentropolis — Simulate Society With Thousands of AI Agents

![](thumbnail.png)

Agentropolis is a real-time, multi-agent urban simulation grounded in Toronto geography.  
The system runs thousands of AI-driven followers, streams tick updates over WebSockets, and renders live behavior on a 3D Mapbox scene.

## Why This Exists

Most city simulations are either purely statistical or purely visual.  
Agentropolis combines both:

- Real map topology (Toronto neighborhoods + work districts).
- Session-scoped synthetic population (archetypes -> followers).
- LLM-driven intent at group level, rule-based follower dynamics at individual level.
- Deterministic fallback paths so simulation continues during model failures.

## Architecture

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy async + `asyncpg`
- PostgreSQL (Neon)
- Alembic migrations
- Railtracks agent orchestration

Core modules:

- `backend/src/api/*`: REST endpoints for sessions, ticks, events, followers, posts, archetypes, zones.
- `backend/src/simulation/tick_orchestrator.py`: per-tick orchestration and broadcast flow.
- `backend/src/agents/*`: archetype decision agent, event designer, tweet generation, fallback logic.
- `backend/src/db/*`: ORM models, query helpers, async engine lifecycle.
- `backend/src/ws/*`: WebSocket endpoint + connection manager heartbeat.

### Frontend

- Next.js 15 + React 19 + TypeScript
- Zustand state store
- Mapbox GL JS 3D rendering

Core modules:

- `frontend/src/store/simulationStore.ts`: session lifecycle, tick loop, WS event handling.
- `frontend/src/api/client.ts`: typed REST and WS client wrappers.
- `frontend/src/world/toronto-mapbox.ts`: terrain/buildings/follower layer + flyover behavior.
- `frontend/src/components/*`: HUD, toolkit, welcome, map container.
- `frontend/src/avatar/*`: deterministic avatar resolution + creator schema.

## Agent Model

### Tier 1: Archetype Decision

- One LLM call per large demographic
- Input includes:
  - recent memories
  - follower aggregate stats
  - relationship summaries
  - active events/effects
  - neighborhood/work location context
- Output: structured action list (`work`, `commute`, `eat`, `sleep`, `shop`, `exercise`, `socialize`, `post`, `attend_event`, `visit_family`).

### Tier 2: Follower Variation

- Rule-based updates for position and happiness to keep runtime stable and deterministic.
- Event effects can override normal movement (industry stay-home, global stay-home, gathering-zone pull).
- Optional tweet generation for sampled followers (rate scaled by event multipliers).

## Event System

Event injection endpoint:

- `POST /api/sessions/{session_id}/events`

Flow:

1. User submits narrative prompt (for example, "Transit strike across downtown").
2. Event-designer agent maps narrative -> structured mechanical levers.
3. Effects are stored with optional `duration_ticks` and computed `end_time`.
4. Tick pipeline applies active effects each hour until expiration.

## API Surface

Session lifecycle:

- `POST /api/sessions`
- `GET /api/sessions/{session_id}`
- `DELETE /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/resume`
- `POST /api/sessions/{session_id}/pause`

Simulation + data:

- `POST /api/sessions/{session_id}/tick`
- `POST /api/sessions/{session_id}/events`
- `GET /api/sessions/{session_id}/followers`
- `POST /api/sessions/{session_id}/followers` (custom avatar join)
- `GET /api/sessions/{session_id}/posts`
- `GET /api/sessions/{session_id}/archetypes`
- `GET /api/zones`
- `GET /api/zones/residential`
- `GET /api/zones/work-districts`

OpenAPI docs:

- `/docs`
- `/redoc`

## WebSocket Contract

Endpoint:

- `ws://<host>/ws/{session_id}`

Client -> server:

- `{"type":"subscribe"}`
- `{"type":"pong"}` (heartbeat ack)

Server -> client:

- `subscribed`
- `ping`
- `tick_start`
- `tick_archetype_decision`
- `tick_archetype_update`
- `tick_complete`
- `error`

Behavior note: when the last client disconnects, the session is auto-paused.

## Data Model

Primary tables:

- `sessions`
- `archetypes`
- `followers`
- `companies`
- `relationships`
- `events`
- `memories`
- `posts`
- `demographics`
- `locations` (shared reference data)

Most entities are session-scoped with composite keys like `(session_id, follower_id)` and cascade deletion from `sessions`.

## Procedural Avatar System

Followers use either:

- `avatar_seed` (deterministic generation), or
- `avatar_params` (custom authored avatar)

Avatar fields include skin tone, body type, hair texture/style/color, outfit, outfit color, and accessories.

The same schema powers seeded agents and user-created entrants, so one rendering pipeline handles both.

Reference spec: [docs/PROCEDURAL_AVATAR_SYSTEM.md](docs/PROCEDURAL_AVATAR_SYSTEM.md)

## Local Development

### Prerequisites

- Python 3.12+
- `uv` (recommended)
- Node.js 20+
- PostgreSQL (Neon URL expected)
- OpenAI API key
- Mapbox token

### 1) Configure backend env

Create `.env` at repository root:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
OPENAI_API_KEY=sk-...
NEON_DB=postgresql://user:password@host/dbname?sslmode=require
YOUR_NEON_API_KEY=napi_...  # optional
```

### 2) Run backend

```bash
cd backend
uv pip install -e .
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Configure frontend env

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN=your_mapbox_token
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4) Run frontend

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Testing

Backend tests:

```bash
cd backend
uv run pytest
```
