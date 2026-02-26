from datetime import datetime, timedelta


def add_business_days(start_date: datetime, business_days: int) -> datetime:
    current_date = start_date
    added_days = 0

    while added_days < business_days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:
            added_days += 1

    return current_date
