import caldav
import uuid
import pytz
from datetime import datetime, timedelta
from loguru import logger
from config import settings
from models import ParsedEvent


class YandexCalendarClient:
    def __init__(self):
        self.url = "https://caldav.yandex.ru"
        self.username = settings.yandex_username
        self.password = settings.yandex_app_password
        self.client = None

    def _get_client(self) -> caldav.DAVClient:
        if self.client is None:
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password,
            )
        return self.client

    def _get_principal(self):
        return self._get_client().principal()

    def get_calendars(self) -> list:
        principal = self._get_principal()
        return principal.calendars()

    def create_event(self, event: ParsedEvent) -> str:
        principal = self._get_principal()
        calendars = principal.calendars()
        
        calendar = calendars[0]
        logger.info(f"Using calendar: {calendar.name} ({calendar.url})")

        tz = pytz.timezone(settings.timezone)
        start_dt = tz.localize(datetime.strptime(f"{event.start_date} {event.start_time}", "%Y-%m-%d %H:%M"))
        
        if event.end_date and event.end_time:
            end_dt = tz.localize(datetime.strptime(f"{event.end_date} {event.end_time}", "%Y-%m-%d %H:%M"))
        else:
            end_dt = start_dt + timedelta(minutes=event.duration_minutes or 60)

        start_utc = start_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")
        end_utc = end_dt.astimezone(pytz.utc).strftime("%Y%m%dT%H%M%SZ")

        uid = str(uuid.uuid4())
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Calemdar//RU
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
SUMMARY:{event.title}
DTSTART:{start_utc}
DTEND:{end_utc}
DESCRIPTION:{event.description or ''}
END:VEVENT
END:VCALENDAR"""

        logger.debug(f"iCal content:\n{ical}")
        calendar.save_event(ical)
        logger.info(f"Created Yandex event: {event.title} on {event.start_date} at {event.start_time} {settings.timezone}")
        return event.title
