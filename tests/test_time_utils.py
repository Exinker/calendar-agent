import pytest
from datetime import datetime, timedelta
import pytz
from time_utils import get_current_datetime, get_current_datetime_str, get_date_context, validate_date_range
from config import settings


class TestTimeUtils:
    def test_get_current_datetime_returns_aware_datetime(self):
        dt = get_current_datetime()
        assert dt.tzinfo is not None

    def test_get_current_datetime_str_format(self):
        s = get_current_datetime_str()
        assert len(s) > 0
        assert "2026" in s or "2025" in s or "2027" in s

    def test_get_date_context_contains_keys(self):
        ctx = get_date_context()
        assert "current_datetime" in ctx
        assert "today" in ctx
        assert "tomorrow" in ctx
        assert "day_after_tomorrow" in ctx
        assert "next_monday" in ctx
        assert "timezone" in ctx

    def test_get_date_context_dates_are_correct(self):
        ctx = get_date_context()
        today = datetime.strptime(ctx["today"], "%Y-%m-%d")
        tomorrow = datetime.strptime(ctx["tomorrow"], "%Y-%m-%d")
        assert (tomorrow - today).days == 1

    def test_validate_date_range_accepts_today(self):
        ctx = get_date_context()
        assert validate_date_range(ctx["today"]) is True

    def test_validate_date_range_accepts_tomorrow(self):
        ctx = get_date_context()
        assert validate_date_range(ctx["tomorrow"]) is True

    def test_validate_date_range_rejects_far_past(self):
        assert validate_date_range("2020-01-01") is False

    def test_validate_date_range_rejects_far_future(self):
        assert validate_date_range("2030-01-01") is False
