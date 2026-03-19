"""
Tests now target WispHubTicketService directly (mocking HTTP calls)
instead of the legacy tickets_service module.
"""

import pytest
import respx
import httpx
from app.services.providers.wisphub.wisphub_ticket_service import (
    WispHubTicketService,
)
from app.core.config import settings
from app.schemas.tickets import TicketCreate

MOCK_WISPHUB_TICKET_DETAIL = {
    "id_ticket": 500,
    "asunto": "Internet Lento",
    "estado": "Abierto",
    "prioridad": "2",
    "fecha_estimada_inicio": "2026-02-26 10:00",
    "fecha_estimada_fin": "2026-02-28 10:00",
    "respuestas": None,
}

MOCK_WISPHUB_TICKETS_LIST = {
    "results": [
        {
            "id_ticket": 1,
            "asunto": "Test",
            "estado": "Abierto",
            "prioridad": "2",
            "fecha_estimada_inicio": "2026-02-26 10:00",
            "fecha_estimada_fin": "2026-02-28 10:00",
            "respuestas": None,
            "servicio": {"zona": {"id": 10}},
        },
        {
            "id_ticket": 2,
            "asunto": "Test",
            "estado": "Abierto",
            "prioridad": "2",
            "fecha_estimada_inicio": "2026-02-26 10:00",
            "fecha_estimada_fin": "2026-02-28 10:00",
            "respuestas": None,
            "servicio": {"zona": {"id": 10}},
        },
        {
            "id_ticket": 3,
            "asunto": "Test",
            "estado": "Abierto",
            "prioridad": "2",
            "fecha_estimada_inicio": "2026-02-26 10:00",
            "fecha_estimada_fin": "2026-02-28 10:00",
            "respuestas": None,
            "servicio": {"zona": {"id": 10}},
        },
    ]
}


def _make_gateway():
    return WispHubTicketService(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_TICKET_DETAIL)
    )

    gateway = _make_gateway()
    ticket = await gateway.get_ticket(500)

    assert ticket is not None
    assert ticket.ticket_id == 500
    assert ticket.subject == "Internet Lento"


@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_not_found():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(404, json={})
    )

    gateway = _make_gateway()
    ticket = await gateway.get_ticket(999)
    assert ticket is None


@pytest.mark.asyncio
@respx.mock
async def test_zone_has_three_open_tickets_true():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_TICKETS_LIST)
    )

    gateway = _make_gateway()
    is_blocked = await gateway.zone_has_three_open_tickets(10)
    assert is_blocked is True


@pytest.mark.asyncio
@respx.mock
async def test_zone_has_three_open_tickets_false():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_TICKETS_LIST)
    )

    gateway = _make_gateway()
    is_blocked = await gateway.zone_has_three_open_tickets(99)  # Different zone
    assert is_blocked is False


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_success():
    mock_created = MOCK_WISPHUB_TICKET_DETAIL.copy()
    mock_created["id_ticket"] = 999

    respx.post(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(201, json=mock_created)
    )

    gateway = _make_gateway()
    new_ticket = TicketCreate(
        service_id=100,
        subject="Internet Lento",
        description="El cliente dice que el internet esta lento",
        technician_id=5,
    )

    ticket = await gateway.create_ticket(new_ticket)

    assert ticket is not None
    assert ticket.ticket_id == 999
    assert ticket.subject == "Internet Lento"
