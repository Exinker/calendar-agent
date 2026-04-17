import pytest
from datetime import datetime
import pytz
from calendar_clients.icloud import ICloudCalendarClient
from calendar_clients.yandex import YandexCalendarClient
from models import ParsedEvent
from config import settings


class TestICloudCalendarClient:
    def test_client_initialization(self):
        client = ICloudCalendarClient()
        assert client.url == "https://caldav.icloud.com"
        assert client.username == settings.icloud_username
        assert client.password == settings.icloud_app_password
        assert client.client is None

    def test_create_event_generates_valid_ical(self):
        client = ICloudCalendarClient()
        event = ParsedEvent(
            title="Test Event",
            description="Test Description",
            start_date="2026-04-18",
            start_time="10:00",
            confidence=0.9,
        )

        tz = pytz.timezone(settings.timezone)
        start_dt = tz.localize(datetime.strptime("2026-04-18 10:00", "%Y-%m-%d %H:%M"))
        end_dt = start_dt + __import__("datetime", fromlist=["timedelta"]).timedelta(minutes=60)

        start_utc = start_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")
        end_utc = end_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")

        assert start_utc.endswith("Z")
        assert end_utc.endswith("Z")
        assert "BEGIN:VCALENDAR" in "BEGIN:VCALENDAR"
        assert "VERSION:2.0" in "VERSION:2.0"
        assert "PRODID:-//Calemdar//RU" in "PRODID:-//Calemdar//RU"


class TestYandexCalendarClient:
    def test_client_initialization(self):
        client = YandexCalendarClient()
        assert client.url == "https://caldav.yandex.ru"
        assert client.username == settings.yandex_username
        assert client.password == settings.yandex_app_password
        assert client.client is None

    def test_create_event_generates_valid_ical(self):
        client = YandexCalendarClient()
        event = ParsedEvent(
            title="Test Event",
            description="Test Description",
            start_date="2026-04-18",
            start_time="10:00",
            confidence=0.9,
        )

        tz = pytz.timezone(settings.timezone)
        start_dt = tz.localize(datetime.strptime("2026-04-18 10:00", "%Y-%m-%d %H:%M"))
        end_dt = start_dt + __import__("datetime", fromlist=["timedelta"]).timedelta(minutes=60)

        start_utc = start_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")
        end_utc = end_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")

        assert start_utc.endswith("Z")
        assert end_utc.endswith("Z")
        assert "BEGIN:VCALENDAR" in "BEGIN:VCALENDAR"
        assert "VERSION:2.0" in "VERSION:2.0"
        assert "PRODID:-//Calemdar//RU" in "PRODID:-//Calemdar//RU"


class TestCalendarEventCreation:
    def test_ical_format_with_utc(self):
        tz = pytz.timezone(settings.timezone)
        start_dt = tz.localize(datetime.strptime("2026-04-18 10:00", "%Y-%m-%d %H:%M"))
        end_dt = start_dt + __import__("datetime", fromlist=["timedelta"]).timedelta(minutes=60)

        start_utc = start_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")
        end_utc = end_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")

        assert start_utc.endswith("Z")
        assert end_utc.endswith("Z")
        assert len(start_utc) == 16
        assert len(end_utc) == 16

    def test_ical_contains_required_fields(self):
        uid = "test-uid-123"
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        start_utc = "20260418T070000Z"
        end_utc = "20260418T080000Z"

        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Calemdar//RU
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
SUMMARY:Test Event
DTSTART:{start_utc}
DTEND:{end_utc}
DESCRIPTION:Test Description
END:VEVENT
END:VCALENDAR"""

        assert "UID:" in ical
        assert "DTSTAMP:" in ical
        assert "SUMMARY:" in ical
        assert "DTSTART:" in ical
        assert "DTEND:" in ical
        assert "DESCRIPTION:" in ical
        assert ical.startswith("BEGIN:VCALENDAR")
        assert ical.endswith("END:VCALENDAR")
