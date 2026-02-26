import pytest
from unittest.mock import patch
from app.schemas.tickets import TicketResponse
from app.schemas.responses.response_actions import ResponseAction, TicketAction
from app.core.config import settings

MOCK_TICKET_RESP = TicketResponse(
    ticket_id=50,
    subject="Falla Masiva",
    created_at="2026-02-26 10:00",
    end_date="2026-02-28 10:00",
    status_ticket="Abierto",
    priority="3",
    answer_text=None
)

@pytest.mark.asyncio
@patch("app.api.v1.tickets.get_ticket")
async def test_get_ticket_endpoint_success(mock_get_ticket, async_client):
    mock_get_ticket.return_value = MOCK_TICKET_RESP
    
    response = await async_client.get("/api/v1/tickets/50")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == TicketAction.FOUND
    assert data["data"]["ticket_id"] == 50

@pytest.mark.asyncio
@patch("app.api.v1.tickets.get_ticket")
async def test_get_ticket_endpoint_not_found(mock_get_ticket, async_client):
    mock_get_ticket.return_value = None
    
    response = await async_client.get("/api/v1/tickets/999")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == TicketAction.NOT_FOUND
    assert data["data"] is None

@pytest.mark.asyncio
@patch("app.api.v1.tickets.zone_has_three_open_tickets")
@patch("app.api.v1.tickets.create_ticket")
async def test_create_ticket_endpoint_success(mock_create, mock_zone, async_client):
    mock_zone.return_value = False
    mock_create.return_value = MOCK_TICKET_RESP
    
    # Send Form data since that's how it's modeled
    response = await async_client.post(
        "/api/v1/tickets",
        json={
            "service_id": 100,
            "subject": "Falla Masiva",
            "technician_id": 5,
            "description": "Prueba",
            "zone_id": 2
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == TicketAction.CREATED
    assert data["data"]["ticket_id"] == 50

@pytest.mark.asyncio
@patch("app.api.v1.tickets.zone_has_three_open_tickets")
async def test_create_ticket_endpoint_zone_blocked(mock_zone, async_client):
    mock_zone.return_value = True
    
    response = await async_client.post(
        "/api/v1/tickets",
        json={
            "service_id": 100,
            "subject": "Falla",
            "technician_id": 5,
            "description": "Prueba",
            "zone_id": 2
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["type"] == "info"
    assert data["action"] == TicketAction.ZONE_LIMIT_REACHED
    assert data["data"]["max_tickets"] == settings.MAX_ACTIVE_TICKETS_PER_ZONE

@pytest.mark.asyncio
@patch("app.api.v1.tickets.zone_has_three_open_tickets")
async def test_check_zone_blocked_true(mock_zone, async_client):
    mock_zone.return_value = True
    
    response = await async_client.get("/api/v1/tickets/zone-blocked/5")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["is_blocked"] is True

@pytest.mark.asyncio
@patch("app.api.v1.tickets.zone_has_three_open_tickets")
async def test_check_zone_blocked_false(mock_zone, async_client):
    mock_zone.return_value = False
    
    response = await async_client.get("/api/v1/tickets/zone-blocked/10")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["is_blocked"] is False
