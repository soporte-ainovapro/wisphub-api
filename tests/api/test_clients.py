import pytest
from unittest.mock import patch, AsyncMock
from app.domain.models.clients import ClientResponse

MOCK_API_CLIENT = ClientResponse(
    service_id=1,
    name="John Doe",
    document="111111",
    phone="333",
    address="Some Address",
    city="City",
    locality="Locality",
    payment_status="Al dia",
    zone_id=1,
    antenna_ip="1.1.1.1",
    cut_off_date="2026-01-01",
    outstanding_balance=0,
    lan_interface="eth1",
    internet_plan_name="Plan 1",
    internet_plan_price=40000.0,
    technician_id=1
)

GATEWAY = "app.infrastructure.gateways.wisphub_client_gateway.WispHubClientGateway"

@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_client_by_document", new_callable=AsyncMock)
async def test_get_client_by_document_endpoint_found(mock_get_client, auth_client):
    mock_get_client.return_value = MOCK_API_CLIENT

    response = await auth_client.get("/api/clients/by-document/111111")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "John Doe"

@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_client_by_document", new_callable=AsyncMock)
async def test_get_client_by_document_endpoint_not_found(mock_get_client, auth_client):
    mock_get_client.return_value = None

    response = await auth_client.get("/api/clients/by-document/111111")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_clients", new_callable=AsyncMock)
async def test_get_clients_endpoint_success(mock_get_clients, auth_client):
    mock_get_clients.return_value = [MOCK_API_CLIENT]

    response = await auth_client.get("/api/clients/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

@pytest.mark.asyncio
@patch(f"{GATEWAY}.fetch_clients_by_query", new_callable=AsyncMock)
async def test_search_clients_endpoint_success(mock_fetch, auth_client):
    mock_fetch.return_value = [MOCK_API_CLIENT]
    response = await auth_client.get("/api/clients/search?q=John")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "John Doe"

@pytest.mark.asyncio
@patch(f"{GATEWAY}.fetch_clients_by_query", new_callable=AsyncMock)
async def test_search_clients_endpoint_not_found(mock_fetch, auth_client):
    mock_fetch.return_value = []

    response = await auth_client.get("/api/clients/search?q=Ghost")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
@patch(f"{GATEWAY}.update_client_profile", new_callable=AsyncMock)
async def test_update_client_endpoint_success(mock_update, auth_client):
    mock_update.return_value = True

    payload = {
        "document": "55555",
        "phone": "300123",
        "address": "Nueva Dirección"
    }
    response = await auth_client.put("/api/clients/101", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

@pytest.mark.asyncio
@patch(f"{GATEWAY}.update_client_profile", new_callable=AsyncMock)
async def test_update_client_all_new_fields(mock_update, auth_client):
    """Verifica que los nuevos campos se traducen correctamente al payload de WispHub."""
    mock_update.return_value = True

    payload = {
        "name": "Juan",
        "last_name": "García Ruiz",
        "locality": "Chapinero",
        "city": "Bogotá",
        "balance": "-50000",
    }
    response = await auth_client.put("/api/clients/101", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # Verifica que el gateway recibió los nombres de campo de WispHub, no los nuestros
    called_payload = mock_update.call_args[0][1]
    assert "nombre" in called_payload
    assert "apellidos" in called_payload
    assert "localidad" in called_payload
    assert "ciudad" in called_payload
    assert "saldo" in called_payload
    assert called_payload["nombre"] == "Juan"
    assert called_payload["apellidos"] == "García Ruiz"
    assert called_payload["saldo"] == "-50000"

@pytest.mark.asyncio
@patch(f"{GATEWAY}.update_client_profile", new_callable=AsyncMock)
async def test_update_client_field_mapping(mock_update, auth_client):
    """Verifica el mapeo exacto de todos los campos Python → WispHub."""
    mock_update.return_value = True

    payload = {
        "name": "Ana",
        "last_name": "López",
        "document": "98765432",
        "address": "Av. Siempreviva 742",
        "locality": "Springfield",
        "city": "Medellín",
        "phone": "3109876543",
        "balance": "20000",
    }
    response = await auth_client.put("/api/clients/202", json=payload)
    assert response.status_code == 200

    called_payload = mock_update.call_args[0][1]
    expected_keys = {"nombre", "apellidos", "cedula", "direccion", "localidad", "ciudad", "telefono", "saldo"}
    assert set(called_payload.keys()) == expected_keys
    # Nuestros nombres de campo Python NO deben aparecer en el payload enviado a WispHub
    python_keys = {"name", "last_name", "document", "address", "locality", "city", "phone", "balance"}
    assert not python_keys.intersection(set(called_payload.keys()))

@pytest.mark.asyncio
@patch(f"{GATEWAY}.update_client_profile", new_callable=AsyncMock)
async def test_update_client_endpoint_failed(mock_update, auth_client):
    mock_update.return_value = False

    payload = {
        "document": "9999"
    }
    response = await auth_client.put("/api/clients/999", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_update_client_endpoint_empty(auth_client):
    payload = {}
    response = await auth_client.put("/api/clients/101", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_client_by_service_id", new_callable=AsyncMock)
async def test_verify_client_identity_success(mock_get, auth_client):
    mock_client = MOCK_API_CLIENT.model_copy()
    mock_client.internet_plan_price = 40000.0
    mock_get.return_value = mock_client

    payload = {
        "name": "John Doe",
        "address": "Some Address",
        "internet_plan_price": 40000.0
    }
    response = await auth_client.post("/api/clients/1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "name" in data["matched_fields"]
    assert "address" in data["matched_fields"]
    assert "internet_plan_price" in data["matched_fields"]

@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_client_by_service_id", new_callable=AsyncMock)
async def test_verify_client_identity_failed_mismatch(mock_get, auth_client):
    mock_client = MOCK_API_CLIENT.model_copy()
    mock_client.internet_plan_price = 40000.0
    mock_get.return_value = mock_client

    payload = {
        "name": "John Doe",
        "address": "Some Address",
        "internet_plan_price": 100.0  # Incorrect price
    }
    response = await auth_client.post("/api/clients/1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert "name" in data["matched_fields"]
    assert "address" in data["matched_fields"]
    assert "internet_plan_price" not in data["matched_fields"]

@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_client_by_service_id", new_callable=AsyncMock)
async def test_verify_client_identity_not_enough_fields(mock_get, auth_client):
    mock_get.return_value = MOCK_API_CLIENT.model_copy()

    payload = {"address": "some", "name": "John Doe"}  # Solo 2 campos
    response = await auth_client.post("/api/clients/1/verify", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Se requieren al menos 3 campos" in data["detail"]

@pytest.mark.asyncio
@patch(f"{GATEWAY}.get_client_by_service_id", new_callable=AsyncMock)
async def test_verify_client_identity_not_found(mock_get, auth_client):
    mock_get.return_value = None

    payload = {"name": "Test", "address": "Some", "internet_plan_price": 40.0}
    response = await auth_client.post("/api/clients/999/verify", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
@patch(f"{GATEWAY}.fetch_clients_by_query", new_callable=AsyncMock)
async def test_resolve_client_identity_success(mock_fetch, auth_client):
    mock_client = MOCK_API_CLIENT.model_copy()
    mock_client.internet_plan_price = 40000.0
    mock_fetch.return_value = [mock_client]

    payload = {
        "name": "John Doe",
        "address": "Some Address",
        "internet_plan_price": 40000.0
    }
    response = await auth_client.post("/api/clients/resolve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["service_id"] == 1

@pytest.mark.asyncio
@patch(f"{GATEWAY}.fetch_clients_by_query", new_callable=AsyncMock)
async def test_resolve_client_identity_not_found(mock_fetch, auth_client):
    mock_fetch.return_value = []

    payload = {
        "name": "Ghost",
        "address": "Unknown",
        "internet_plan_price": 100.0
    }
    response = await auth_client.post("/api/clients/resolve", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_resolve_client_identity_not_enough_fields(auth_client):
    payload = {
        "name": "John Doe",
        "address": "Some Address"
    }
    response = await auth_client.post("/api/clients/resolve", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Se requieren al menos 3 campos" in data["detail"]
