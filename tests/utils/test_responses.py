from app.utils.responses import build_client_response
from app.schemas.clients import ClientResponse, ClientAction
from fastapi import HTTPException
import pytest


def test_build_client_response_found():
    # Creamos un cliente de prueba
    client = ClientResponse(
        service_id=123,
        name="Test Client",
        document="12345678",
        phone="555123456",
        address="Test Addr",
        city="City",
        locality="Locality",
        payment_status="Al dia",
        zone_id=1,
        antenna_ip="192.168.1.200",
        cut_off_date="2026-03-01",
        outstanding_balance=0.0,
        lan_interface="ether1",
        internet_plan_name="Plan 10MB",
        technician_id=1,
    )

    response = build_client_response(client)
    assert response == client


def test_build_client_response_not_found():
    with pytest.raises(HTTPException) as excinfo:
        build_client_response(None)
    assert excinfo.value.status_code == 404
