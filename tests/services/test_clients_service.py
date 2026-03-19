"""
These tests now test WispHubClientService directly (mocking the HTTP calls)
instead of the legacy clients_service module.
"""

import pytest
import respx
import httpx
from unittest.mock import AsyncMock
from app.services.providers.wisphub.wisphub_client_service import (
    WispHubClientService,
)
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
            "precio_plan": "40000.00",
            "tecnico": {"id": 5, "nombre": "Tech 1"},
        }
    ],
    "next": None,
}


def _make_gateway():
    mock_plan_service = AsyncMock()
    return WispHubClientService(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
        internet_plan_service=mock_plan_service,
    )


@pytest.mark.asyncio
@respx.mock
async def test_get_client_by_document_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_CLIENT_RESPONSE)
    )

    gateway = _make_gateway()
    client = await gateway.get_client_by_document("12345678")

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
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    gateway = _make_gateway()
    client = await gateway.get_client_by_document("00000000")
    assert client is None


@pytest.mark.asyncio
@respx.mock
async def test_get_client_api_error():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(500, json={"error": "Internal Server Error"})
    )

    gateway = _make_gateway()
    client = await gateway.get_client_by_document("1234")
    assert client is None


@pytest.mark.asyncio
@respx.mock
async def test_get_clients_list_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_CLIENT_RESPONSE)
    )

    gateway = _make_gateway()
    clients = await gateway.get_clients()

    assert isinstance(clients, list)
    assert len(clients) == 1
    assert clients[0].document == "12345678"


# ---------------------------------------------------------------------------
# get_client_by_phone
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_get_client_by_phone_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_CLIENT_RESPONSE)
    )

    gateway = _make_gateway()
    client = await gateway.get_client_by_phone("+55 5123456")

    assert client is not None
    assert client.phone == "555123456"


@pytest.mark.asyncio
@respx.mock
async def test_get_client_by_phone_not_found():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    gateway = _make_gateway()
    client = await gateway.get_client_by_phone("0000000")
    assert client is None


# ---------------------------------------------------------------------------
# get_client_by_service_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_get_client_by_service_id_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_CLIENT_RESPONSE)
    )

    gateway = _make_gateway()
    client = await gateway.get_client_by_service_id("100")

    assert client is not None
    assert client.service_id == 100


@pytest.mark.asyncio
async def test_get_client_by_service_id_not_found():
    from unittest.mock import patch as _patch

    gateway = _make_gateway()
    with _patch.object(gateway, "_fetch_service_id", return_value=None):
        client = await gateway.get_client_by_service_id("9999")
    assert client is None


# ---------------------------------------------------------------------------
# fetch_clients_by_query
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_clients_by_query_found():
    from unittest.mock import patch as _patch
    gateway = _make_gateway()

    mock_client = ClientResponse(
        service_id=100, name="Test Client", document="12345678", phone="555123456",
        address="Fake St 123", city="Springfield", locality="North",
        payment_status="Al dia", zone_id=1, antenna_ip="1.1.1.1",
        cut_off_date="2026-03-01", outstanding_balance=0.0,
        lan_interface="ether1", internet_plan_name="Plan Default",
        internet_plan_price=40000.0, technician_id=5,
    )

    with _patch.object(gateway, "get_clients", return_value=[mock_client]):
        results = await gateway.fetch_clients_by_query("test client")

    assert len(results) == 1
    assert results[0].name == "Test Client"


@pytest.mark.asyncio
async def test_fetch_clients_by_query_no_match():
    from unittest.mock import patch as _patch
    gateway = _make_gateway()

    mock_client = ClientResponse(
        service_id=100, name="Test Client", document="12345678", phone="555123456",
        address="Fake St 123", city="Springfield", locality="North",
        payment_status="Al dia", zone_id=1, antenna_ip="1.1.1.1",
        cut_off_date="2026-03-01", outstanding_balance=0.0,
        lan_interface="ether1", internet_plan_name="Plan Default",
        internet_plan_price=40000.0, technician_id=5,
    )

    with _patch.object(gateway, "get_clients", return_value=[mock_client]):
        results = await gateway.fetch_clients_by_query("ghost xyz")  # no match

    assert results == []


# ---------------------------------------------------------------------------
# update_client_profile
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_update_client_profile_success():
    respx.put(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={})
    )

    gateway = _make_gateway()
    result = await gateway.update_client_profile(100, {"nombre": "Nuevo Nombre"})
    assert result is True


@pytest.mark.asyncio
@respx.mock
async def test_update_client_profile_failed():
    respx.put(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(400, json={})
    )

    gateway = _make_gateway()
    result = await gateway.update_client_profile(100, {"nombre": "Nuevo Nombre"})
    assert result is False


# ---------------------------------------------------------------------------
# resolve business logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_success():
    from unittest.mock import patch as _patch
    from app.schemas.clients import ClientResolveRequest

    gateway = _make_gateway()
    match_client = ClientResponse(
        service_id=100, name="Test Client", document="12345678", phone="555123456",
        address="Fake St 123", city="Springfield", locality="North",
        payment_status="Al dia", zone_id=1, antenna_ip="1.1.1.1",
        cut_off_date="2026-03-01", outstanding_balance=0.0,
        lan_interface="ether1", internet_plan_name="Plan Default",
        internet_plan_price=40000.0, technician_id=5,
    )

    with _patch.object(gateway, "fetch_clients_by_query", return_value=[match_client]):
        request = ClientResolveRequest(
            name="Test Client", address="Fake St 123", internet_plan_price=40000.0
        )
        result = await gateway.resolve(request)

    assert result.service_id == 100


@pytest.mark.asyncio
async def test_resolve_not_enough_fields():
    from app.schemas.clients import ClientResolveRequest
    import pytest
    from fastapi import HTTPException

    gateway = _make_gateway()
    with pytest.raises(HTTPException) as exc:
        await gateway.resolve(ClientResolveRequest(name="A", address="B"))  # solo 2 campos
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_resolve_no_candidates_raises_404():
    from unittest.mock import patch as _patch
    from app.schemas.clients import ClientResolveRequest
    import pytest
    from fastapi import HTTPException

    gateway = _make_gateway()
    with _patch.object(gateway, "fetch_clients_by_query", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            await gateway.resolve(
                ClientResolveRequest(name="Ghost", address="Nowhere", internet_plan_price=99.0)
            )
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# verify business logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verify_success():
    from unittest.mock import patch as _patch
    from app.schemas.clients import ClientVerifyRequest

    gateway = _make_gateway()
    stored_client = ClientResponse(
        service_id=100, name="Test Client", document="12345678", phone="555123456",
        address="Fake St 123", city="Springfield", locality="North",
        payment_status="Al dia", zone_id=1, antenna_ip="1.1.1.1",
        cut_off_date="2026-03-01", outstanding_balance=0.0,
        lan_interface="ether1", internet_plan_name="Plan Default",
        internet_plan_price=40000.0, technician_id=5,
    )

    with _patch.object(gateway, "get_client_by_service_id", return_value=stored_client):
        result = await gateway.verify(
            100,
            ClientVerifyRequest(name="Test Client", address="Fake St 123", internet_plan_price=40000.0),
        )

    assert result["is_valid"] is True
    assert "name" in result["matched_fields"]
    assert "address" in result["matched_fields"]
    assert "internet_plan_price" in result["matched_fields"]


@pytest.mark.asyncio
async def test_verify_price_fallback_via_plan_service():
    """When client.internet_plan_price is None, verify fetches price from internet_plan_service."""
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock
    from app.schemas.clients import ClientVerifyRequest
    from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse

    mock_plan_service = AsyncMock()
    gateway = WispHubClientService(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
        internet_plan_service=mock_plan_service,
    )

    # Client stored without price — it must be resolved via the plan service
    stored_client = ClientResponse(
        service_id=100, name="Test Client", document="12345678", phone="555123456",
        address="Fake St 123", city="Springfield", locality="North",
        payment_status="Al dia", zone_id=1, antenna_ip="1.1.1.1",
        cut_off_date="2026-03-01", outstanding_balance=0.0,
        lan_interface="ether1", internet_plan_name="Plan Default",
        internet_plan_price=None,  # ← triggers fallback
        technician_id=5,
    )
    mock_plan_service.list_internet_plans = _AsyncMock(
        return_value=[InternetPlanListItem(plan_id=10, name="Plan Default", type="PPPOE")]
    )
    mock_plan_service.get_pppoe_plan = _AsyncMock(
        return_value=InternetPlanResponse(name="Plan Default", price=40000.0, download_speed="10", upload_speed="2")
    )

    with _patch.object(gateway, "get_client_by_service_id", return_value=stored_client):
        result = await gateway.verify(
            100,
            ClientVerifyRequest(name="Test Client", address="Fake St 123", internet_plan_price=40000.0),
        )

    assert result["is_valid"] is True
    assert "internet_plan_price" in result["matched_fields"]
    mock_plan_service.list_internet_plans.assert_called_once()
    mock_plan_service.get_pppoe_plan.assert_called_once_with(10)
