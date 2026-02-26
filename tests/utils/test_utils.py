from datetime import datetime
from app.utils.dates import add_business_days
from app.utils.ticket_rules import get_priority

def test_add_business_days():
    # Thursday, 1 day = Friday
    start_date = datetime(2026, 2, 26, 12, 0)
    result = add_business_days(start_date, 1)
    assert result.weekday() == 4
    assert result.day == 27
    
    # Friday, 1 day = Monday
    start_date = datetime(2026, 2, 27, 12, 0)
    result = add_business_days(start_date, 1)
    assert result.weekday() == 0  # 0 is Monday
    assert result.day == 2  # March 2nd
    
def test_get_priority():
    # Baja priority
    assert get_priority("Cambio de Domicilio") == 1
    
    # Alta priority
    assert get_priority("No Tiene Internet") == 3
    
    # Priority not found
    assert get_priority("Asunto Desconocido Que No Existe") is None
