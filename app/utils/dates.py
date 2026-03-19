from datetime import date, datetime, timedelta
from typing import FrozenSet


# ---------------------------------------------------------------------------
# Colombian public holidays
# ---------------------------------------------------------------------------

def _easter_sunday(year: int) -> date:
    """Meeus/Jones/Butcher algorithm — returns Easter Sunday for the given year."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _to_monday(d: date) -> date:
    """Returns d unchanged if it is already Monday, otherwise the next Monday."""
    shift = (7 - d.weekday()) % 7
    return d + timedelta(days=shift)


def get_colombian_holidays(year: int) -> FrozenSet[date]:
    """
    Returns all Colombian public holidays for *year* as a frozenset of date objects.

    Holiday categories:
    - Fijos: fecha invariable (Año Nuevo, Trabajo, Independencia, Boyacá, etc.)
    - Ley Emiliani: se trasladan al lunes siguiente si no caen en lunes.
    - Basados en Pascua: relativos al Domingo de Resurrección; algunos se
      trasladan al lunes siguiente (Ascensión, Corpus Christi, Sagrado Corazón).
    """
    easter = _easter_sunday(year)

    def fixed(month: int, day: int) -> date:
        return date(year, month, day)

    def emiliani(month: int, day: int) -> date:
        return _to_monday(date(year, month, day))

    def from_easter(days: int) -> date:
        return easter + timedelta(days=days)

    def from_easter_monday(days: int) -> date:
        return _to_monday(easter + timedelta(days=days))

    return frozenset({
        # --- Fijos ---
        fixed(1, 1),    # Año Nuevo
        fixed(5, 1),    # Día del Trabajo
        fixed(7, 20),   # Día de la Independencia
        fixed(8, 7),    # Batalla de Boyacá
        fixed(12, 8),   # Inmaculada Concepción
        fixed(12, 25),  # Navidad
        # --- Ley Emiliani ---
        emiliani(1, 6),   # Reyes Magos
        emiliani(3, 19),  # San José
        emiliani(6, 29),  # San Pedro y San Pablo
        emiliani(8, 15),  # Asunción de la Virgen
        emiliani(10, 12), # Día de la Raza
        emiliani(11, 1),  # Todos los Santos
        emiliani(11, 11), # Independencia de Cartagena
        # --- Basados en Pascua (fijos) ---
        from_easter(-3),  # Jueves Santo
        from_easter(-2),  # Viernes Santo
        # --- Basados en Pascua (Ley Emiliani) ---
        from_easter_monday(39), # Ascensión del Señor
        from_easter_monday(60), # Corpus Christi
        from_easter_monday(68), # Sagrado Corazón de Jesús
    })


# ---------------------------------------------------------------------------
# Business-day arithmetic
# ---------------------------------------------------------------------------

def add_business_days(
    start_date: datetime,
    business_days: int,
    holidays: FrozenSet[date] = frozenset(),
) -> datetime:
    current_date = start_date
    added_days = 0

    while added_days < business_days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5 and current_date.date() not in holidays:
            added_days += 1

    return current_date
