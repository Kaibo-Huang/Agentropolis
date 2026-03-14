"""
Integration tests for the Sessions API endpoints.

Uses httpx.AsyncClient + ASGITransport so the FastAPI app runs in-process.
Database calls are mocked via dependency overrides so no real NeonDB connection
is required.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Patch database_url before importing the app so the engine module doesn't
# attempt a real connection during module load.
with patch("src.config.settings") as _mock_settings:
    _mock_settings.database_url = ""
    from src.main import app
    from src.db.engine import get_db


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_session(
    session_id: uuid.UUID | None = None,
    status: str = "paused",
    config: dict | None = None,
) -> MagicMock:
    """Build a mock Session ORM object."""
    sid = session_id or uuid.uuid4()
    s = MagicMock()
    s.session_id = sid
    s.created_at = datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
    s.virtual_time = datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
    s.status = status
    s.config = config or {"total_population": 100, "archetype_count": 10, "company_count": 20}
    return s


@pytest.fixture
def mock_db():
    """Yield a mock AsyncSession."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def client_factory(mock_db):
    """Return a factory that creates an AsyncClient with DB overridden."""
    async def _make_client():
        app.dependency_overrides[get_db] = lambda: mock_db
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    yield _make_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper — patch the query layer used by the sessions router
# ---------------------------------------------------------------------------

_SESSIONS_MODULE = "src.api.sessions"


@pytest.mark.asyncio
async def test_health_check():
    """GET /health returns 200 with status ok (no DB dependency)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_session_returns_201(mock_db):
    """POST /api/sessions returns 201 with session_id field."""
    sid = uuid.uuid4()
    session_obj = _make_session(session_id=sid)

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_SESSIONS_MODULE}.create_session", new=AsyncMock(return_value=session_obj)),
        patch(f"{_SESSIONS_MODULE}.get_follower_count", new=AsyncMock(return_value=0)),
        patch(f"{_SESSIONS_MODULE}._SEEDER_AVAILABLE", False),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/sessions", json={})

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == str(sid)
    assert data["status"] == "paused"
    assert "created_at" in data
    assert "virtual_time" in data
    assert "follower_count" in data


@pytest.mark.asyncio
async def test_create_session_with_config(mock_db):
    """POST /api/sessions with explicit config passes values through."""
    sid = uuid.uuid4()
    config = {"total_population": 50, "archetype_count": 5, "company_count": 10}
    session_obj = _make_session(session_id=sid, config=config)

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_SESSIONS_MODULE}.create_session", new=AsyncMock(return_value=session_obj)),
        patch(f"{_SESSIONS_MODULE}.get_follower_count", new=AsyncMock(return_value=0)),
        patch(f"{_SESSIONS_MODULE}._SEEDER_AVAILABLE", False),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/sessions", json={"config": config})

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["config"]["total_population"] == 50


@pytest.mark.asyncio
async def test_get_session_returns_200(mock_db):
    """GET /api/sessions/{id} returns 200 for an existing session."""
    sid = uuid.uuid4()
    session_obj = _make_session(session_id=sid)

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=session_obj)),
        patch(f"{_SESSIONS_MODULE}.get_follower_count", new=AsyncMock(return_value=42)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/sessions/{sid}")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == str(sid)
    assert data["follower_count"] == 42


@pytest.mark.asyncio
async def test_get_session_returns_404_for_missing(mock_db):
    """GET /api/sessions/{id} returns 404 when the session does not exist."""
    sid = uuid.uuid4()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=None)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/sessions/{sid}")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert str(sid) in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_session_returns_204(mock_db):
    """DELETE /api/sessions/{id} returns 204 when deletion succeeds."""
    sid = uuid.uuid4()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_SESSIONS_MODULE}.delete_session", new=AsyncMock(return_value=True)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/sessions/{sid}")

    app.dependency_overrides.clear()

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_session_returns_404_when_not_found(mock_db):
    """DELETE /api/sessions/{id} returns 404 when session doesn't exist."""
    sid = uuid.uuid4()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_SESSIONS_MODULE}.delete_session", new=AsyncMock(return_value=False)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/sessions/{sid}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_resume_session_transitions_to_running(mock_db):
    """POST /api/sessions/{id}/resume transitions paused → running."""
    sid = uuid.uuid4()
    paused_session = _make_session(session_id=sid, status="paused")
    running_session = _make_session(session_id=sid, status="running")

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=paused_session)),
        patch(f"{_SESSIONS_MODULE}.update_session_status", new=AsyncMock(return_value=running_session)),
        patch(f"{_SESSIONS_MODULE}.get_follower_count", new=AsyncMock(return_value=0)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/sessions/{sid}/resume")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "running"


@pytest.mark.asyncio
async def test_resume_already_running_returns_409(mock_db):
    """POST /api/sessions/{id}/resume returns 409 when already running."""
    sid = uuid.uuid4()
    running_session = _make_session(session_id=sid, status="running")

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=running_session)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/sessions/{sid}/resume")

    app.dependency_overrides.clear()

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_pause_session_transitions_to_paused(mock_db):
    """POST /api/sessions/{id}/pause transitions running → paused."""
    sid = uuid.uuid4()
    running_session = _make_session(session_id=sid, status="running")
    paused_session = _make_session(session_id=sid, status="paused")

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=running_session)),
        patch(f"{_SESSIONS_MODULE}.update_session_status", new=AsyncMock(return_value=paused_session)),
        patch(f"{_SESSIONS_MODULE}.get_follower_count", new=AsyncMock(return_value=0)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/sessions/{sid}/pause")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "paused"


@pytest.mark.asyncio
async def test_pause_already_paused_returns_409(mock_db):
    """POST /api/sessions/{id}/pause returns 409 when already paused."""
    sid = uuid.uuid4()
    paused_session = _make_session(session_id=sid, status="paused")

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=paused_session)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/sessions/{sid}/pause")

    app.dependency_overrides.clear()

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_resume_missing_session_returns_404(mock_db):
    """POST /api/sessions/{id}/resume returns 404 for nonexistent session."""
    sid = uuid.uuid4()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_SESSIONS_MODULE}.get_session", new=AsyncMock(return_value=None)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/sessions/{sid}/resume")

    app.dependency_overrides.clear()

    assert response.status_code == 404
