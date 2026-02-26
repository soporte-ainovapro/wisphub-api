import pytest
import respx
import httpx
from app.services.clients_service import get_client_by_document, get_clients, parse_client
from app.core.config import settings
from app.schemas.clients import ClientResponse

MOCK_WISPHUB_CLIENT_RESPONSE = {
    "results": [
        {
            "id_servicio": 100,
            "nombre": "Test Client",
            "cedula": "12345678",
            "telefono": "555123456",
            "direccion": "Fake St 123",
            "ciudad": "Springfield",
            "localidad": "North",
            "estado": "Al dia",
            "zona": {"id": 1, "nombre": "Zone 1"},
            "ip": "1.1.1.1",
            "fecha_corte": "2026-03-01",
            "saldo": 0.0,
            "interfaz_lan": "ether1",
            "plan_internet": {"id": 2, "nombre": "Plan Default"},
            "tecnico": {"id": 5, "nombre": "Tech 1"}
        }
    ]
}

@pytest.mark.asyncio
@respx.mock
async def test_get_client_by_document_success():
    respx.get(
        url__startswith=settings.CLIENTS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_WISPHUB_CLIENT_RESPONSE))
    
    client = await get_client_by_document("12345678")
    
    assert client is not None
    assert isinstance(client, ClientResponse)
    assert client.document == "12345678"
    assert client.name == "Test Client"
    assert client.zone_id == 1
    assert client.internet_plan_name == "Plan Default"
    assert client.technician_id == 5

@pytest.mark.asyncio
@respx.mock
async def test_get_client_by_document_not_found():
    respx.get(
        url__startswith=settings.CLIENTS_URL
    ).mock(return_value=httpx.Response(200, json={"results": []}))
    
    client = await get_client_by_document("00000000")
    
    assert client is None

@pytest.mark.asyncio
@respx.mock
async def test_get_client_api_error():
    respx.get(
        url__startswith=settings.CLIENTS_URL
    ).mock(return_value=httpx.Response(500, json={"error": "Internal Server Error"}))
    
    client = await get_client_by_document("1234")
    assert client is None
    
@pytest.mark.asyncio
@respx.mock
async def test_get_client_timeout():
    respx.get(
        url__startswith=settings.CLIENTS_URL
    ).mock(side_effect=httpx.TimeoutException("Timeout"))
    
    with pytest.raises(httpx.TimeoutException):
        await get_client_by_document("1234")

@pytest.mark.asyncio
@respx.mock
async def test_get_clients_list_success():
    respx.get(
        url__startswith=settings.CLIENTS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_WISPHUB_CLIENT_RESPONSE))
    
    clients = await get_clients()
    
    assert isinstance(clients, list)
    assert len(clients) == 1
    assert clients[0].document == "12345678"
