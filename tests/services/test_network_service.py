import pytest
import respx
import httpx
from app.services.network_service import ping, get_task__id
from app.core.config import settings
from app.schemas.connection_status import ConnectionStatus

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

@pytest.mark.asyncio
@respx.mock
async def test_get_task_id_success():
    respx.post(
        url__startswith=settings.CLIENTS_URL
    ).mock(return_value=httpx.Response(202, json=MOCK_PING_TASK_CREATED))
    
    task_id = await get_task__id(4, 100)
    assert task_id == "123-abc"
    
@pytest.mark.asyncio
@respx.mock
async def test_get_task_id_failed():
    respx.post(
        url__startswith=settings.CLIENTS_URL
    ).mock(return_value=httpx.Response(400, json={}))
    
    task_id = await get_task__id(4, 100)
    assert task_id is None

@pytest.mark.asyncio
@respx.mock
async def test_ping_stable_connection():
    respx.get(
        url__startswith=settings.TASKS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_TASK_RESULT_SUCCESS))
    
    status = await ping("123-abc")
    assert status == ConnectionStatus.stable
    
@pytest.mark.asyncio
@respx.mock
async def test_ping_intermittent_connection():
    respx.get(
        url__startswith=settings.TASKS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_TASK_RESULT_INTERMITTENT))
    
    status = await ping("123-abc")
    assert status == ConnectionStatus.intermittent
    
@pytest.mark.asyncio
@respx.mock
async def test_ping_no_internet_connection():
    respx.get(
        url__startswith=settings.TASKS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_TASK_RESULT_NO_INTERNET))
    
    status = await ping("123-abc")
    assert status == ConnectionStatus.no_internet
