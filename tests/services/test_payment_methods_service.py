import pytest
import respx
import httpx
from unittest.mock import patch, AsyncMock
from app.services.providers.wisphub.wisphub_payment_method_service import (
    WispHubPaymentMethodService,
)
from app.core.config import settings

MOCK_WISPHUB_PAYMENT_METHODS = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        {"id": 1, "nombre": "Efectivo"},
        {"id": 2, "nombre": "Transferencia"},
    ],
}

_GATEWAY_PATH = (
    "app.services.providers.wisphub.wisphub_payment_method_service"
    ".WispHubPaymentMethodService"
)


def _make_gateway():
    return WispHubPaymentMethodService(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@pytest.mark.asyncio
@respx.mock
async def test_list_payment_methods_success():
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_WISPHUB_PAYMENT_METHODS)
    )

    gateway = _make_gateway()
    methods = await gateway.list_payment_methods()

    assert methods is not None
    assert len(methods) == 2
    assert methods[0].id == 1
    assert methods[0].name == "Efectivo"
    assert methods[1].id == 2
    assert methods[1].name == "Transferencia"


@pytest.mark.asyncio
@patch(f"{_GATEWAY_PATH}.list_payment_methods", new_callable=AsyncMock)
async def test_list_payment_methods_api_error(mock_list):
    mock_list.return_value = None

    gateway = _make_gateway()
    methods = await gateway.list_payment_methods()
    assert methods is None


@pytest.mark.asyncio
@patch(f"{_GATEWAY_PATH}.list_payment_methods", new_callable=AsyncMock)
async def test_list_payment_methods_empty_results(mock_list):
    mock_list.return_value = []

    gateway = _make_gateway()
    methods = await gateway.list_payment_methods()
    assert methods == []
