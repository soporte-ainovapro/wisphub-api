import pytest
from unittest.mock import patch
from app.schemas.responses.response_actions import ResponseAction, NetworkAction
from app.schemas.connection_status import ConnectionStatus

@pytest.mark.asyncio
@patch("app.api.v1.network.get_task__id")
async def test_create_ping_endpoint_success(mock_task_id, auth_client):
    mock_task_id.return_value = "123-abc"
    
    response = await auth_client.post(
        "/api/v1/100/ping/",
        json={"pings": 4}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == NetworkAction.PING_CREATED
    assert data["data"]["task_id"] == "123-abc"

@pytest.mark.asyncio
@patch("app.api.v1.network.ping")
async def test_get_ping_result_endpoint_stable(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.stable
    
    response = await auth_client.get("/api/v1/ping/123-abc/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["type"] == "success"
    assert data["action"] == NetworkAction.STABLE

@pytest.mark.asyncio
@patch("app.api.v1.network.ping")
async def test_get_ping_result_endpoint_intermittent(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.intermittent
    
    response = await auth_client.get("/api/v1/ping/123-abc/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["type"] == "info"
    assert data["action"] == NetworkAction.INTERMITTENT

@pytest.mark.asyncio
@patch("app.api.v1.network.ping")
async def test_get_ping_result_endpoint_no_internet(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.no_internet
    
    response = await auth_client.get("/api/v1/ping/123-abc/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["type"] == "info"
    assert data["action"] == NetworkAction.NO_INTERNET

@pytest.mark.asyncio
@patch("app.api.v1.network.ping")
async def test_get_ping_result_endpoint_error(mock_ping, auth_client):
    mock_ping.return_value = ConnectionStatus.error
    
    response = await auth_client.get("/api/v1/ping/123-abc/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is False
    assert data["type"] == "error"
    assert data["action"] == NetworkAction.PING_FAILED
