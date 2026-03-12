"""
Tests now target WispHubNetworkGateway directly (mocking HTTP calls)
instead of the legacy network_service module.
"""
import pytest
import respx
import httpx
from app.infrastructure.gateways.wisphub_network_gateway import WispHubNetworkGateway
from app.core.config import settings
from app.domain.models.connection_status import ConnectionStatus

MOCK_PING_TASK_CREATED = {
    "task_id": "123-abc",
    "status": "PROCESS"
}

MOCK_TASK_RESULT_SUCCESS = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {"ping-1.1.1.1": {"sent": 4, "received": 4}}
        ]
    }
}

MOCK_TASK_RESULT_INTERMITTENT = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {"ping-1.1.1.1": {"sent": 4, "received": 2}}
        ]
    }
}

MOCK_TASK_RESULT_NO_INTERNET = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {"ping-1.1.1.1": {"sent": 4, "received": 0}}
        ]
    }
}

def _make_gateway():
    return WispHubNetworkGateway(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )

@pytest.mark.asyncio
@respx.mock
async def test_get_task_id_success():
    respx.post(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(202, json=MOCK_PING_TASK_CREATED))

    gateway = _make_gateway()
    task_id = await gateway._get_task_id(4, 100)
    assert task_id == "123-abc"

@pytest.mark.asyncio
@respx.mock
async def test_get_task_id_failed():
    respx.post(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(400, json={}))

    gateway = _make_gateway()
    task_id = await gateway._get_task_id(4, 100)
    assert task_id is None

@pytest.mark.asyncio
@respx.mock
async def test_ping_stable_connection():
    respx.get(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(200, json=MOCK_TASK_RESULT_SUCCESS))

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.stable

@pytest.mark.asyncio
@respx.mock
async def test_ping_intermittent_connection():
    respx.get(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(200, json=MOCK_TASK_RESULT_INTERMITTENT))

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.intermittent

@pytest.mark.asyncio
@respx.mock
async def test_ping_no_internet_connection():
    respx.get(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(200, json=MOCK_TASK_RESULT_NO_INTERNET))

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.no_internet
