import pytest
from unittest.mock import patch, AsyncMock
from app.domain.models.internet_plans import InternetPlanListItem, InternetPlanResponse

MOCK_PLANS = [
    InternetPlanListItem(plan_id=1, name="Plan 1", type="PPPOE")
]

GATEWAY = "app.infrastructure.gateways.wisphub_internet_plan_gateway.WispHubInternetPlanGateway"

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
async def test_get_plan_detail_pppoe_success(mock_get_pppoe, mock_list_plans, auth_client):
    mock_list_plans.return_value = [
        InternetPlanListItem(plan_id=1, name="PPPOE_Plan", type="PPPOE")
    ]
    mock_get_pppoe.return_value = InternetPlanResponse(
        name="PPPOE_Plan", price=40000.0,
        download_speed="10", upload_speed="2"
    )

    response = await auth_client.get("/api/internet-plans/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PPPOE_Plan"
