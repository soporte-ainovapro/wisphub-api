from app.utils.responses import build_client_response
from app.schemas.clients import ClientResponse
from app.schemas.responses.response_actions import ResponseAction, ClientAction

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
        technician_id=1
    )
    
    response = build_client_response(client)
    assert response.ok is True
    assert response.type == "success"
    assert response.action == ClientAction.FOUND
    assert response.data == client
    
def test_build_client_response_not_found():
    response = build_client_response(None)
    assert response.ok is True
    assert response.type == "info"
    assert response.action == ClientAction.NOT_FOUND
    assert response.data is None
