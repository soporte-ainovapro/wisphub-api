import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.connection_status import ConnectionStatus

GATEWAY = "app.services.providers.wisphub.wisphub_network_service.WispHubNetworkService"


@pytest.mark.asyncio
@patch(f"{GATEWAY}._get_task_id", new_callable=AsyncMock)
async def test_create_ping_endpoint_success(mock_task_id, auth_client):
    mock_task_id.return_value = "123-abc"

    response = await auth_client.post("/api/100/ping/", json={"pings": 4})
    assert response.status_code == 200

    data = response.json()
    assert data["task_id"] == "123-abc"


@pytest.mark.asyncio
@patch(f"{GATEWAY}._get_task_id", new_callable=AsyncMock)
async def test_create_ping_endpoint_failed(mock_task_id, auth_client):
    mock_task_id.return_value = None

    response = await auth_client.post("/api/100/ping/", json={"pings": 4})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@patch(f"{GATEWAY}._poll_ping", new_callable=AsyncMock)
async def test_get_ping_result_endpoint_stable(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.stable

    response = await auth_client.get("/api/ping/123-abc/")
    assert response.status_code == 200

    data = response.json()
    assert data["result"] == "stable"


@pytest.mark.asyncio
@patch(f"{GATEWAY}._poll_ping", new_callable=AsyncMock)
async def test_get_ping_result_endpoint_no_internet(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.no_internet

    response = await auth_client.get("/api/ping/123-abc/")
    assert response.status_code == 200

    data = response.json()
    assert data["result"] == "no_internet"


@pytest.mark.asyncio
@patch(f"{GATEWAY}._poll_ping", new_callable=AsyncMock)
async def test_get_ping_result_endpoint_error(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.error

    response = await auth_client.get("/api/ping/123-abc/")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
