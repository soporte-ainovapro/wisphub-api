import pytest
from unittest.mock import patch
from app.schemas.clients import ClientResponse
from app.schemas.responses.response_actions import ResponseAction, ClientAction

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

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_client_by_document")
async def test_get_client_by_document_endpoint_found(mock_get_client, auth_client):
    mock_get_client.return_value = MOCK_API_CLIENT
    
    response = await auth_client.get("/api/v1/clients/by-document/111111")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.FOUND
    assert data["data"]["name"] == "John Doe"

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_client_by_document")
async def test_get_client_by_document_endpoint_not_found(mock_get_client, auth_client):
    mock_get_client.return_value = None
    
    response = await auth_client.get("/api/v1/clients/by-document/111111")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.NOT_FOUND
    assert data["data"] is None

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_clients")
async def test_get_clients_endpoint_success(mock_get_clients, auth_client):
    mock_get_clients.return_value = [MOCK_API_CLIENT]
    
    response = await auth_client.get("/api/v1/clients/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.LISTED
    assert len(data["data"]) == 1

@pytest.mark.asyncio
@patch("app.api.v1.clients.fetch_clients_by_query")
async def test_search_clients_endpoint_success(mock_fetch, auth_client):
    mock_fetch.return_value = [MOCK_API_CLIENT]
    response = await auth_client.get("/api/v1/clients/search?q=John")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.LISTED
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "John Doe"

@pytest.mark.asyncio
@patch("app.api.v1.clients.fetch_clients_by_query")
async def test_search_clients_endpoint_not_found(mock_fetch, auth_client):
    mock_fetch.return_value = []
    
    response = await auth_client.get("/api/v1/clients/search?q=Ghost")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.NOT_FOUND
    assert data["data"] == []

@pytest.mark.asyncio
@patch("app.api.v1.clients.update_client_profile")
async def test_update_client_endpoint_success(mock_update, auth_client):
    mock_update.return_value = True
    
    payload = {
        "document": "55555",
        "phone": "300123"
    }
    response = await auth_client.put("/api/v1/clients/101", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.UPDATED

@pytest.mark.asyncio
@patch("app.api.v1.clients.update_client_profile")
async def test_update_client_endpoint_failed(mock_update, auth_client):
    mock_update.return_value = False
    
    payload = {
        "document": "9999"
    }
    response = await auth_client.put("/api/v1/clients/999", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["action"] == ClientAction.UPDATE_FAILED

@pytest.mark.asyncio
async def test_update_client_endpoint_empty(auth_client):
    # No patching needed since it should fail before touching WispHub
    payload = {}
    response = await auth_client.put("/api/v1/clients/101", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == ClientAction.UPDATE_FAILED

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_client_by_service_id")
async def test_verify_client_identity_success(mock_get, auth_client):
    # Set up mock with plan price so it effectively matches.
    mock_client = MOCK_API_CLIENT.model_copy()
    mock_client.internet_plan_price = 40000.0
    mock_get.return_value = mock_client
    
    payload = {
        "name": "John Doe",
        "address": "Some Address",
        "internet_plan_price": 40000.0
    }
    response = await auth_client.post("/api/v1/clients/1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.VERIFIED
    assert data["data"]["is_valid"] is True
    assert "name" in data["data"]["matched_fields"]
    assert "address" in data["data"]["matched_fields"]
    assert "internet_plan_price" in data["data"]["matched_fields"]

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_client_by_service_id")
async def test_verify_client_identity_failed_mismatch(mock_get, auth_client):
    mock_client = MOCK_API_CLIENT.model_copy()
    mock_client.internet_plan_price = 40000.0
    mock_get.return_value = mock_client
    
    payload = {
        "name": "John Doe",
        "address": "Some Address",
        "internet_plan_price": 100.0  # Incorrect price
    }
    response = await auth_client.post("/api/v1/clients/1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.VERIFICATION_FAILED
    assert data["data"]["is_valid"] is False
    assert "name" in data["data"]["matched_fields"]
    assert "address" in data["data"]["matched_fields"]
    assert "internet_plan_price" not in data["data"]["matched_fields"]

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_client_by_service_id")
async def test_verify_client_identity_not_enough_fields(mock_get, auth_client):
    mock_get.return_value = MOCK_API_CLIENT.model_copy()
    
    payload = {"address": "some", "name": "John Doe"}  # Solo 2 campos
    response = await auth_client.post("/api/v1/clients/1/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["action"] == ClientAction.VERIFICATION_FAILED
    assert "Se requieren al menos 3 campos" in data["message"]

@pytest.mark.asyncio
@patch("app.api.v1.clients.get_client_by_service_id")
async def test_verify_client_identity_not_found(mock_get, auth_client):
    mock_get.return_value = None
    
    payload = {"name": "Test", "address": "Some", "internet_plan_price": 40.0}
    response = await auth_client.post("/api/v1/clients/999/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["action"] == ClientAction.NOT_FOUND

@pytest.mark.asyncio
@patch("app.api.v1.clients.fetch_clients_by_query")
async def test_resolve_client_identity_success(mock_fetch, auth_client):
    mock_client = MOCK_API_CLIENT.model_copy()
    mock_client.internet_plan_price = 40000.0
    mock_fetch.return_value = [mock_client]

    payload = {
        "name": "John Doe",
        "address": "Some Address",
        "internet_plan_price": 40000.0
    }
    response = await auth_client.post("/api/v1/clients/resolve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == ClientAction.VERIFIED
    assert data["data"]["service_id"] == 1

@pytest.mark.asyncio
@patch("app.api.v1.clients.fetch_clients_by_query")
async def test_resolve_client_identity_not_found(mock_fetch, auth_client):
    mock_fetch.return_value = []

    payload = {
        "name": "Ghost",
        "address": "Unknown",
        "internet_plan_price": 100.0
    }
    response = await auth_client.post("/api/v1/clients/resolve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["action"] == ClientAction.NOT_FOUND

@pytest.mark.asyncio
async def test_resolve_client_identity_not_enough_fields(auth_client):
    payload = {
        "name": "John Doe",
        "address": "Some Address"
    }
    response = await auth_client.post("/api/v1/clients/resolve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["action"] == ClientAction.VERIFICATION_FAILED
    assert "Se requieren al menos 3 campos" in data["message"]
