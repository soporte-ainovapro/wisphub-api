from datetime import date, datetime
from app.utils.dates import add_business_days, get_colombian_holidays
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


def test_add_business_days_skips_holidays():
    # Viernes Santo 2026 = Apr 3. Starting Wed Apr 1, 2 business days
    # without holidays: Fri Apr 3 + Mon Apr 6 = Mon Apr 6
    # with holidays (Apr 3 skipped): Mon Apr 6 + Tue Apr 7 = Tue Apr 7
    holidays_2026 = get_colombian_holidays(2026)
    start = datetime(2026, 4, 1, 9, 0)  # Wednesday
    result = add_business_days(start, 2, holidays_2026)
    assert result.date() == date(2026, 4, 7)  # Tuesday (Fri Santo + Lun skipped)


def test_get_colombian_holidays_2026():
    holidays = get_colombian_holidays(2026)

    # Fixed holidays
    assert date(2026, 1, 1) in holidays   # Año Nuevo
    assert date(2026, 5, 1) in holidays   # Día del Trabajo
    assert date(2026, 7, 20) in holidays  # Independencia
    assert date(2026, 8, 7) in holidays   # Batalla de Boyacá
    assert date(2026, 12, 8) in holidays  # Inmaculada Concepción
    assert date(2026, 12, 25) in holidays # Navidad

    # Easter 2026 = April 5 (Sunday)
    assert date(2026, 4, 2) in holidays   # Jueves Santo (Apr 5 - 3)
    assert date(2026, 4, 3) in holidays   # Viernes Santo (Apr 5 - 2)

    # Ley Emiliani: Jan 6 (Tue) -> Mon Jan 12
    assert date(2026, 1, 12) in holidays
    # Ley Emiliani: Mar 19 (Thu) -> Mon Mar 23
    assert date(2026, 3, 23) in holidays

    # Ascensión: Easter+39 = May 14 (Thu) -> Mon May 18
    assert date(2026, 5, 18) in holidays
    # Corpus Christi: Easter+60 = Jun 4 (Thu) -> Mon Jun 8
    assert date(2026, 6, 8) in holidays
    # Sagrado Corazón: Easter+68 = Jun 12 (Fri) -> Mon Jun 15
    assert date(2026, 6, 15) in holidays

    assert len(holidays) == 18


def test_get_colombian_holidays_count_invariant():
    # Cada año debe tener entre 17 y 18 feriados (puede haber coincidencias de fecha
    # cuando un feriado Ley Emiliani y uno basado en Pascua caen el mismo lunes).
    for year in range(2024, 2031):
        count = len(get_colombian_holidays(year))
        assert 17 <= count <= 18, f"Unexpected holiday count {count} for {year}"


def test_get_priority():
    # Baja priority
    assert get_priority("Cambio de Domicilio") == 1

    # Alta priority
    assert get_priority("No Tiene Internet") == 3

    # Priority not found
    assert get_priority("Asunto Desconocido Que No Existe") is None
