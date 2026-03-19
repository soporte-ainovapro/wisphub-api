"""
Tests now target WispHubInternetPlanService directly (mocking HTTP calls)
instead of the legacy internet_plans_service module.
"""

import pytest
import respx
import httpx
from app.services.providers.wisphub.wisphub_internet_plan_service import (
    WispHubInternetPlanService,
)
from app.core.config import settings

MOCK_PLANS_LIST = {
    "results": [
        {"id": 10, "nombre": "Plan 10MB", "tipo": "PPPOE"},
        {"id": 20, "nombre": "Plan 20MB", "tipo": "SIMPLE QUEUE"},
    ]
}


def _make_gateway():
    return WispHubInternetPlanService(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@pytest.mark.asyncio
@respx.mock
async def test_list_internet_plans_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_PLANS_LIST)
    )

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
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(500, json={})
    )

    gateway = _make_gateway()
    plan = await gateway.get_pppoe_plan(999)
    assert plan is None


# ---------------------------------------------------------------------------
# get_queue_plan
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_get_queue_plan_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={
            "nombre": "Plan 20MB",
            "precio": "20000.00",
            "bajada": "20",
            "subida": "5",
        })
    )

    gateway = _make_gateway()
    plan = await gateway.get_queue_plan(20)

    assert plan is not None
    assert plan.name == "Plan 20MB"
    assert plan.download_speed == "20"


@pytest.mark.asyncio
@respx.mock
async def test_get_queue_plan_not_found():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(404, json={})
    )

    gateway = _make_gateway()
    plan = await gateway.get_queue_plan(999)
    assert plan is None


# ---------------------------------------------------------------------------
# get_plan_detail branching (PCQ / PPPOE / SIMPLE QUEUE)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_get_plan_detail_pppoe():
    from unittest.mock import patch as _patch, AsyncMock as _AM
    from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse

    gateway = _make_gateway()
    with _patch.object(gateway, "list_internet_plans", new=_AM(return_value=[
        InternetPlanListItem(plan_id=10, name="Plan 10MB", type="PPPOE")
    ])):
        with _patch.object(gateway, "get_pppoe_plan", new=_AM(
            return_value=InternetPlanResponse(name="Plan 10MB", price=40000.0, download_speed="10", upload_speed="2")
        )):
            result = await gateway.get_plan_detail(10)
    assert result.name == "Plan 10MB"


@pytest.mark.asyncio
async def test_get_plan_detail_simple_queue():
    from unittest.mock import patch as _patch, AsyncMock as _AM
    from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse

    gateway = _make_gateway()
    with _patch.object(gateway, "list_internet_plans", new=_AM(return_value=[
        InternetPlanListItem(plan_id=20, name="Plan 20MB", type="SIMPLE QUEUE")
    ])):
        with _patch.object(gateway, "get_queue_plan", new=_AM(
            return_value=InternetPlanResponse(name="Plan 20MB", price=20000.0, download_speed="20", upload_speed="5")
        )):
            result = await gateway.get_plan_detail(20)
    assert result.name == "Plan 20MB"


@pytest.mark.asyncio
async def test_get_plan_detail_pcq():
    from unittest.mock import patch as _patch, AsyncMock as _AM
    from app.schemas.internet_plans import InternetPlanListItem

    gateway = _make_gateway()
    with _patch.object(gateway, "list_internet_plans", new=_AM(return_value=[
        InternetPlanListItem(plan_id=30, name="PCQ Plan", type="PCQ")
    ])):
        result = await gateway.get_plan_detail(30)
    assert result["type"] == "PCQ"
    assert "note" in result


@pytest.mark.asyncio
async def test_get_plan_detail_not_found_raises_404():
    import pytest as _pytest
    from fastapi import HTTPException
    from unittest.mock import patch as _patch, AsyncMock as _AM

    gateway = _make_gateway()
    with _patch.object(gateway, "list_internet_plans", new=_AM(return_value=[])):
        with _pytest.raises(HTTPException) as exc:
            await gateway.get_plan_detail(999)
    assert exc.value.status_code == 404
