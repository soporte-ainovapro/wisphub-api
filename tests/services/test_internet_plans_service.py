import pytest
import respx
import httpx
from app.services.internet_plans_service import list_internet_plans, get_plan_type
from app.core.config import settings

MOCK_PLANS_LIST = {
    "results": [
        {"id": 10, "nombre": "Plan 10MB", "tipo": "PPPOE"},
        {"id": 20, "nombre": "Plan 20MB", "tipo": "SIMPLE QUEUE"}
    ]
}

@pytest.mark.asyncio
@respx.mock
async def test_list_internet_plans_success():
    respx.get(
        url__startswith=settings.PLANS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_PLANS_LIST))
    
    import app.services.internet_plans_service as ips
    plans = await list_internet_plans()
    
    assert plans is not None
    assert len(plans) == 2
    assert plans[0].plan_id == 10
    assert plans[0].type == "PPPOE"

@pytest.mark.asyncio
@respx.mock
async def test_get_plan_type():
    respx.get(
        url__startswith=settings.PLANS_URL
    ).mock(return_value=httpx.Response(200, json=MOCK_PLANS_LIST))
    
    import app.services.internet_plans_service as ips
    plan_type = await get_plan_type(20)
    assert plan_type == "SIMPLE QUEUE"
    
    plan_type_invalid = await get_plan_type(999)
    assert plan_type_invalid is None
