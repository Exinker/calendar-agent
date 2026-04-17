from datetime import datetime, timedelta
import pytz
from typing import Optional
from config import settings


def get_current_datetime() -> datetime:
    tz = pytz.timezone(settings.timezone)
    return datetime.now(tz)


def get_current_datetime_str() -> str:
    dt = get_current_datetime()
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def get_date_context() -> dict:
    dt = get_current_datetime()
    today = dt.strftime("%Y-%m-%d")
    tomorrow = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after_tomorrow = (dt + timedelta(days=2)).strftime("%Y-%m-%d")

    next_monday = dt + timedelta(days=(7 - dt.weekday()) % 7)
    if next_monday <= dt:
        next_monday += timedelta(days=7)

    return {
        "current_datetime": get_current_datetime_str(),
        "today": today,
        "tomorrow": tomorrow,
        "day_after_tomorrow": day_after_tomorrow,
        "next_monday": next_monday.strftime("%Y-%m-%d"),
        "timezone": settings.timezone,
    }


def validate_date_range(date_str: str) -> bool:
    event_date = datetime.strptime(date_str, "%Y-%m-%d")
    now = get_current_datetime().replace(tzinfo=None)
    min_date = now - timedelta(days=30)
    max_date = now + timedelta(days=730)
    return min_date <= event_date <= max_date
