import pytest
from unittest.mock import patch
from app.core.config import settings
from app.schemas.responses.response_actions import ClientAction


# ---------------------------------------------------------------------------
# Authentication flow tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(async_client):
    """Valid credentials should return a 200 with an access_token."""
    response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": settings.API_USERNAME, "password": "wisphub2024"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client):
    """Wrong password must return 401."""
    response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": settings.API_USERNAME, "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_username(async_client):
    """Unknown username must return 401."""
    response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "hacker", "password": "wisphub2024"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected route guard tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_protected_route_without_token(async_client):
    """Calling a protected route with no token must return 401."""
    response = await async_client.get("/api/v1/clients/")
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.api.v1.clients.get_clients")
async def test_protected_route_with_valid_token(mock_get_clients, auth_client):
    """Calling a protected route with a valid Bearer token must return 200."""
    mock_get_clients.return_value = []
    response = await auth_client.get("/api/v1/clients/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(async_client):
    """Calling a protected route with a garbage token must return 401."""
    response = await async_client.get(
        "/api/v1/clients/",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Public routes — must be accessible without auth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint_is_public(async_client):
    """/health must remain accessible without authentication."""
    response = await async_client.get("/health")
    assert response.status_code == 200
