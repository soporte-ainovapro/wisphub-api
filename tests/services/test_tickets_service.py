import pytest
import respx
import httpx
from app.services.tickets_service import get_ticket, create_ticket, zone_has_three_open_tickets
from app.core.config import settings
from app.schemas.tickets import TicketCreate, TicketResponse

MOCK_WISPHUB_TICKET_DETAIL = {
    "id_ticket": 500,
    "asunto": "Internet Lento",
    "estado": "Abierto",
    "prioridad": "2",
    "fecha_estimada_inicio": "2026-02-26 10:00",
    "fecha_estimada_fin": "2026-02-28 10:00",
    "respuestas": [
        {"respuesta": "Test answer history"}
    ]
}

MOCK_WISPHUB_TICKETS_LIST = {
    "results": [
        {"id_ticket": 1, "servicio": {"zona": {"id": 10}}},
        {"id_ticket": 2, "servicio": {"zona": {"id": 10}}},
        {"id_ticket": 3, "servicio": {"zona": {"id": 10}}}
    ]
}

@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_success():
    respx.get(
        url__startswith=settings.TICKETS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_WISPHUB_TICKET_DETAIL))
    
    ticket = await get_ticket(500)
    
    assert ticket is not None
    assert ticket.ticket_id == 500
    assert ticket.subject == "Internet Lento"
    assert ticket.answer_text is None
    
@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_not_found():
    respx.get(
        url__startswith=settings.TICKETS_URL
    ).mock(return_value=httpx.Response(404, json={}))
    
    ticket = await get_ticket(999)
    assert ticket is None

@pytest.mark.asyncio
@respx.mock
async def test_zone_has_three_open_tickets_true():
    respx.get(
        url__startswith=settings.TICKETS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_WISPHUB_TICKETS_LIST))
    
    is_blocked = await zone_has_three_open_tickets(10)
    assert is_blocked is True
    
@pytest.mark.asyncio
@respx.mock
async def test_zone_has_three_open_tickets_false():
    respx.get(
        url__startswith=settings.TICKETS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_WISPHUB_TICKETS_LIST))
    
    is_blocked = await zone_has_three_open_tickets(99) # Different zone
    assert is_blocked is False

@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_success():
    mock_created = MOCK_WISPHUB_TICKET_DETAIL.copy()
    mock_created["id_ticket"] = 999
    
    respx.post(
        url__startswith=settings.TICKETS_URL
    ).mock(return_value=httpx.Response(201, json=mock_created))
    
    new_ticket = TicketCreate(
        service_id=100,
        subject="Internet Lento",
        description="El cliente dice que el internet esta lento",
        technician_id=5
    )
    
    ticket = await create_ticket(new_ticket)
    
    assert ticket is not None
    assert ticket.ticket_id == 999
    assert ticket.subject == "Internet Lento"
