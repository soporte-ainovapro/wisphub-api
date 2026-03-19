import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.payment_methods import PaymentMethodResponse

MOCK_METHODS = [
    PaymentMethodResponse(id=1, name="Efectivo"),
    PaymentMethodResponse(id=2, name="Transferencia"),
]

GATEWAY = "app.services.providers.wisphub.wisphub_payment_method_service.WispHubPaymentMethodService"


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_payment_methods", new_callable=AsyncMock)
async def test_list_payment_methods_success(mock_list, auth_client):
    mock_list.return_value = MOCK_METHODS

    response = await auth_client.get("/api/payment-methods/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "Efectivo"
    assert data[1]["id"] == 2


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_payment_methods", new_callable=AsyncMock)
async def test_list_payment_methods_not_found(mock_list, auth_client):
    mock_list.return_value = None

    response = await auth_client.get("/api/payment-methods/")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
@patch(f"{GATEWAY}.list_payment_methods", new_callable=AsyncMock)
async def test_list_payment_methods_empty(mock_list, auth_client):
    mock_list.return_value = []

    response = await auth_client.get("/api/payment-methods/")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_payment_methods_requires_api_key(async_client):
    response = await async_client.get("/api/payment-methods/")
    assert response.status_code in {401, 403}
