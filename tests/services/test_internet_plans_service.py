"""
Tests now target WispHubInternetPlanGateway directly (mocking HTTP calls)
instead of the legacy internet_plans_service module.
"""
import pytest
import respx
import httpx
from app.infrastructure.gateways.wisphub_internet_plan_gateway import WispHubInternetPlanGateway
from app.core.config import settings

MOCK_PLANS_LIST = {
    "results": [
        {"id": 10, "nombre": "Plan 10MB", "tipo": "PPPOE"},
        {"id": 20, "nombre": "Plan 20MB", "tipo": "SIMPLE QUEUE"}
    ]
}

def _make_gateway():
    return WispHubInternetPlanGateway(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )

@pytest.mark.asyncio
@respx.mock
async def test_list_internet_plans_success():
    respx.get(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(200, json=MOCK_PLANS_LIST))

    gateway = _make_gateway()
    plans = await gateway.list_internet_plans()

    assert plans is not None
    assert len(plans) == 2
    assert plans[0].plan_id == 10
    assert plans[0].type == "PPPOE"

@pytest.mark.asyncio
@respx.mock
async def test_get_pppoe_plan_not_found():
    """Tests that a 500 response from WispHub returns None for plan details."""
    respx.get(
        url__startswith=settings.WISPHUB_NET_HOST
    ).mock(return_value=httpx.Response(500, json={}))

    gateway = _make_gateway()
    plan = await gateway.get_pppoe_plan(999)
    assert plan is None
