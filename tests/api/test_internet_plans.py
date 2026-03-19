import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse

MOCK_PLANS = [InternetPlanListItem(plan_id=1, name="Plan 1", type="PPPOE")]

GATEWAY = "app.services.providers.wisphub.wisphub_internet_plan_service.WispHubInternetPlanService"


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_internet_plans", new_callable=AsyncMock)
async def test_list_internet_plans_endpoint_success(mock_list_plans, auth_client):
    mock_list_plans.return_value = MOCK_PLANS

    response = await auth_client.get("/api/internet-plans/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Plan 1"


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_internet_plans", new_callable=AsyncMock)
async def test_list_internet_plans_endpoint_not_found(mock_list_plans, auth_client):
    mock_list_plans.return_value = None

    response = await auth_client.get("/api/internet-plans/")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_internet_plans", new_callable=AsyncMock)
async def test_get_plan_detail_not_found(mock_list, auth_client):
    mock_list.return_value = []

    response = await auth_client.get("/api/internet-plans/999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_internet_plans", new_callable=AsyncMock)
@patch(f"{GATEWAY}.get_pppoe_plan", new_callable=AsyncMock)
async def test_get_plan_detail_pppoe_success(
    mock_get_pppoe, mock_list_plans, auth_client
):
    mock_list_plans.return_value = [
        InternetPlanListItem(plan_id=1, name="PPPOE_Plan", type="PPPOE")
    ]
    mock_get_pppoe.return_value = InternetPlanResponse(
        name="PPPOE_Plan", price=40000.0, download_speed="10", upload_speed="2"
    )

    response = await auth_client.get("/api/internet-plans/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PPPOE_Plan"


# ---------------------------------------------------------------------------
# SIMPLE QUEUE plan detail
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_internet_plans", new_callable=AsyncMock)
@patch(f"{GATEWAY}.get_queue_plan", new_callable=AsyncMock)
async def test_get_plan_detail_simple_queue_success(mock_get_queue, mock_list_plans, auth_client):
    mock_list_plans.return_value = [
        InternetPlanListItem(plan_id=2, name="Queue_Plan", type="SIMPLE QUEUE")
    ]
    mock_get_queue.return_value = InternetPlanResponse(
        name="Queue_Plan", price=25000.0, download_speed="5", upload_speed="1"
    )

    response = await auth_client.get("/api/internet-plans/2")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Queue_Plan"
    assert data["price"] == 25000.0


# ---------------------------------------------------------------------------
# PCQ plan detail
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_internet_plans", new_callable=AsyncMock)
async def test_get_plan_detail_pcq_success(mock_list_plans, auth_client):
    mock_list_plans.return_value = [
        InternetPlanListItem(plan_id=3, name="PCQ_Plan", type="PCQ")
    ]

    response = await auth_client.get("/api/internet-plans/3")
    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"] == 3
    assert data["type"] == "PCQ"
    assert "note" in data


# ---------------------------------------------------------------------------
# Unauthenticated (403)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_internet_plan_endpoints_require_api_key(async_client):
    """All internet-plan endpoints must reject requests without X-API-Key."""
    endpoints = [
        ("GET", "/api/internet-plans/"),
        ("GET", "/api/internet-plans/1"),
    ]
    for method, path in endpoints:
        response = await async_client.request(method, path)
        assert response.status_code in {401, 403}, f"{method} {path} should return 401 or 403"
