import pytest
from unittest.mock import patch
from app.schemas.internet_plans import InternetPlanListItem
from app.schemas.responses.response_actions import ResponseAction, PlanAction

MOCK_PLANS = [
    InternetPlanListItem(plan_id=1, name="Plan 1", type="PPPOE")
]

@pytest.mark.asyncio
@patch("app.api.v1.internet_plans.list_internet_plans")
async def test_list_internet_plans_endpoint_success(mock_list_plans, auth_client):
    mock_list_plans.return_value = MOCK_PLANS
    
    response = await auth_client.get("/api/v1/internet-plans/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == PlanAction.LISTED
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Plan 1"

@pytest.mark.asyncio
@patch("app.api.v1.internet_plans.list_internet_plans")
async def test_list_internet_plans_endpoint_not_found(mock_list_plans, auth_client):
    mock_list_plans.return_value = None
    
    response = await auth_client.get("/api/v1/internet-plans/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == PlanAction.NOT_FOUND

@pytest.mark.asyncio
@patch("app.api.v1.internet_plans.get_plan_type")
async def test_get_plan_detail_not_found(mock_get_type, auth_client):
    mock_get_type.return_value = None
    
    response = await auth_client.get("/api/v1/internet-plans/999")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == PlanAction.NOT_FOUND

@pytest.mark.asyncio
@patch("app.api.v1.internet_plans.list_internet_plans")
@patch("app.api.v1.internet_plans.get_pppoe_plan")
async def test_get_plan_detail_pppoe_success(mock_get_pppoe, mock_list_plans, auth_client):
    from app.schemas.internet_plans import InternetPlanListItem, InternetPlanResponse
    mock_list_plans.return_value = [
        InternetPlanListItem(plan_id=1, name="PPPOE_Plan", type="PPPOE")
    ]
    mock_get_pppoe.return_value = InternetPlanResponse(
        name="PPPOE_Plan", price=40000.0,
        download_speed="10", upload_speed="2"
    )

    response = await auth_client.get("/api/v1/internet-plans/1")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["action"] == PlanAction.FOUND
