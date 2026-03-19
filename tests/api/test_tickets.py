import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.tickets import TicketResponse
from app.core.config import settings

MOCK_TICKET_RESP = TicketResponse(
    ticket_id=50,
    subject="Falla Masiva",
    created_at="2026-02-26 10:00",
    end_date="2026-02-28 10:00",
    status_ticket="Abierto",
    priority="3",
    answer_text=None,
)

GATEWAY = "app.services.providers.wisphub.wisphub_ticket_service.WispHubTicketService"


@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_ticket", new_callable=AsyncMock)
async def test_get_ticket_endpoint_success(mock_get_ticket, auth_client):
    mock_get_ticket.return_value = MOCK_TICKET_RESP

    response = await auth_client.get("/api/tickets/50")
    assert response.status_code == 200

    data = response.json()
    assert data["ticket_id"] == 50


@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_ticket", new_callable=AsyncMock)
async def test_get_ticket_endpoint_not_found(mock_get_ticket, auth_client):
    mock_get_ticket.return_value = None

    response = await auth_client.get("/api/tickets/999")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@patch(f"{GATEWAY}.zone_has_three_open_tickets", new_callable=AsyncMock)
@patch(f"{GATEWAY}.create_ticket", new_callable=AsyncMock)
async def test_create_ticket_endpoint_success(mock_create, mock_zone, auth_client):
    mock_zone.return_value = False
    mock_create.return_value = MOCK_TICKET_RESP

    response = await auth_client.post(
        "/api/tickets",
        json={
            "service_id": 100,
            "subject": "Falla Masiva",
            "technician_id": 5,
            "description": "Prueba",
            "zone_id": 2,
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert data["ticket_id"] == 50


@pytest.mark.asyncio
@patch(f"{GATEWAY}.zone_has_three_open_tickets", new_callable=AsyncMock)
async def test_create_ticket_endpoint_zone_blocked(mock_zone, auth_client):
    mock_zone.return_value = True

    response = await auth_client.post(
        "/api/tickets",
        json={
            "service_id": 100,
            "subject": "Falla",
            "technician_id": 5,
            "description": "Prueba",
            "zone_id": 2,
        },
    )
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "máximo" in data["detail"].lower()


@pytest.mark.asyncio
@patch(f"{GATEWAY}.zone_has_three_open_tickets", new_callable=AsyncMock)
async def test_check_zone_blocked_true(mock_zone, auth_client):
    mock_zone.return_value = True

    response = await auth_client.get("/api/tickets/zone-blocked/5")
    assert response.status_code == 200

    data = response.json()
    assert data["is_blocked"] is True


@pytest.mark.asyncio
@patch(f"{GATEWAY}.zone_has_three_open_tickets", new_callable=AsyncMock)
async def test_check_zone_blocked_false(mock_zone, auth_client):
    mock_zone.return_value = False

    response = await auth_client.get("/api/tickets/zone-blocked/10")
    assert response.status_code == 200

    data = response.json()
    assert data["is_blocked"] is False


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_ticket_subjects_endpoint(auth_client):
    response = await auth_client.get("/api/tickets/subjects")
    assert response.status_code == 200
    data = response.json()
    assert "by_priority" in data
    assert "all" in data
    assert "low" in data["by_priority"]
    assert "high" in data["by_priority"]
    assert isinstance(data["all"], list)
    assert len(data["all"]) > 0


# ---------------------------------------------------------------------------
# Unauthenticated (403)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ticket_endpoints_require_api_key(async_client):
    """All ticket endpoints must reject requests without X-API-Key."""
    endpoints = [
        ("POST", "/api/tickets"),
        ("GET", "/api/tickets/subjects"),
        ("GET", "/api/tickets/zone-blocked/1"),
        ("GET", "/api/tickets/1"),
    ]
    for method, path in endpoints:
        response = await async_client.request(method, path, json={})
        assert response.status_code in {401, 403}, f"{method} {path} should return 401 or 403"
