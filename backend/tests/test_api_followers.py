"""
Integration tests for the Followers API endpoints.

GET  /api/sessions/{id}/followers  — list with pagination
POST /api/sessions/{id}/followers  — create follower with custom avatar
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

with patch("src.config.settings") as _mock_settings:
    _mock_settings.database_url = ""
    from src.main import app
    from src.db.engine import get_db


_FOLLOWERS_MODULE = "src.api.followers"
_QUERIES_MODULE = "src.db.queries"


def _make_session(session_id: uuid.UUID | None = None) -> MagicMock:
    sid = session_id or uuid.uuid4()
    s = MagicMock()
    s.session_id = sid
    return s


def _make_follower(
    session_id: uuid.UUID,
    follower_id: int = 1,
    archetype_id: int = 1,
) -> MagicMock:
    f = MagicMock()
    f.session_id = session_id
    f.follower_id = follower_id
    f.archetype_id = archetype_id
    f.name = "Test Follower"
    f.age = 30
    f.gender = "male"
    f.race = "White"
    f.home_position = [43.65, -79.38]
    f.work_position = [43.66, -79.39]
    f.position = [43.65, -79.38]
    f.status_ailments = []
    f.happiness = 0.5
    f.volatility = 0.5
    f.avatar_seed = 12345
    f.avatar_params = None
    return f


@pytest.mark.asyncio
async def test_list_followers_returns_200(tmp_path):
    """GET /api/sessions/{id}/followers returns 200 with follower list."""
    sid = uuid.uuid4()
    mock_db = AsyncMock()
    session_obj = _make_session(session_id=sid)
    follower1 = _make_follower(sid, follower_id=1)
    follower2 = _make_follower(sid, follower_id=2)

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_QUERIES_MODULE}.get_session", new=AsyncMock(return_value=session_obj)),
        patch(f"{_QUERIES_MODULE}.get_followers_for_session", new=AsyncMock(return_value=[follower1, follower2])),
        patch(f"{_QUERIES_MODULE}.get_follower_count", new=AsyncMock(return_value=2)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/sessions/{sid}/followers")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["followers"]) == 2
    assert data["offset"] == 0
    assert data["limit"] == 50  # default


@pytest.mark.asyncio
async def test_list_followers_pagination_params():
    """GET /api/sessions/{id}/followers respects offset and limit query params."""
    sid = uuid.uuid4()
    mock_db = AsyncMock()
    session_obj = _make_session(session_id=sid)

    app.dependency_overrides[get_db] = lambda: mock_db

    captured_offset = []
    captured_limit = []

    async def mock_get_followers(db, session_id, offset, limit):
        captured_offset.append(offset)
        captured_limit.append(limit)
        return []

    with (
        patch(f"{_QUERIES_MODULE}.get_session", new=AsyncMock(return_value=session_obj)),
        patch(f"{_QUERIES_MODULE}.get_followers_for_session", side_effect=mock_get_followers),
        patch(f"{_QUERIES_MODULE}.get_follower_count", new=AsyncMock(return_value=100)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/sessions/{sid}/followers?offset=20&limit=10"
            )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["offset"] == 20
    assert data["limit"] == 10
    assert captured_offset[0] == 20
    assert captured_limit[0] == 10


@pytest.mark.asyncio
async def test_list_followers_returns_404_for_missing_session():
    """GET /api/sessions/{id}/followers returns 404 when session not found."""
    sid = uuid.uuid4()
    mock_db = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_QUERIES_MODULE}.get_session", new=AsyncMock(return_value=None)):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/sessions/{sid}/followers")

    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_followers_limit_max_is_200():
    """GET /api/sessions/{id}/followers rejects limit > 200."""
    sid = uuid.uuid4()
    mock_db = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_QUERIES_MODULE}.get_session", new=AsyncMock(return_value=_make_session(sid))):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/sessions/{sid}/followers?limit=201"
            )

    app.dependency_overrides.clear()

    assert response.status_code == 422  # validation error


@pytest.mark.asyncio
async def test_list_followers_offset_cannot_be_negative():
    """GET /api/sessions/{id}/followers rejects negative offset."""
    sid = uuid.uuid4()
    mock_db = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch(f"{_QUERIES_MODULE}.get_session", new=AsyncMock(return_value=_make_session(sid))):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/sessions/{sid}/followers?offset=-1"
            )

    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_follower_response_fields_present():
    """GET followers response includes all required fields for each follower."""
    sid = uuid.uuid4()
    mock_db = AsyncMock()
    session_obj = _make_session(session_id=sid)
    follower = _make_follower(sid, follower_id=7, archetype_id=3)

    app.dependency_overrides[get_db] = lambda: mock_db

    with (
        patch(f"{_QUERIES_MODULE}.get_session", new=AsyncMock(return_value=session_obj)),
        patch(f"{_QUERIES_MODULE}.get_followers_for_session", new=AsyncMock(return_value=[follower])),
        patch(f"{_QUERIES_MODULE}.get_follower_count", new=AsyncMock(return_value=1)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/sessions/{sid}/followers")

    app.dependency_overrides.clear()

    data = response.json()
    f = data["followers"][0]
    required_fields = [
        "follower_id", "archetype_id", "name", "age", "gender", "race",
        "home_position", "work_position", "position",
        "status_ailments", "happiness", "volatility",
    ]
    for field in required_fields:
        assert field in f, f"Missing field '{field}' in follower response"

    assert f["follower_id"] == 7
    assert f["archetype_id"] == 3
    assert f["happiness"] == 0.5
