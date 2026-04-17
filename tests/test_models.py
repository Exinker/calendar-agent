import pytest
from datetime import datetime
from models import ParsedEvent, ParsedEventsList


class TestParsedEvent:
    def test_minimal_valid_event(self):
        event = ParsedEvent(
            title="Meeting",
            start_date="2026-04-18",
            start_time="15:00",
            confidence=0.9,
        )
        assert event.title == "Meeting"
        assert event.start_date == "2026-04-18"
        assert event.start_time == "15:00"
        assert event.duration_minutes == 60
        assert event.is_recurring is False
        assert event.needs_clarification is False

    def test_full_event(self):
        event = ParsedEvent(
            title="Conference",
            description="Annual tech conference",
            start_date="2026-05-01",
            start_time="09:00",
            end_date="2026-05-01",
            end_time="17:00",
            duration_minutes=480,
            is_recurring=False,
            recurrence_rule=None,
            reminder_minutes_before=30,
            confidence=0.95,
            needs_clarification=False,
            clarification_question=None,
        )
        assert event.title == "Conference"
        assert event.description == "Annual tech conference"
        assert event.duration_minutes == 480

    def test_invalid_start_date_format(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            ParsedEvent(
                title="Test",
                start_date="18-04-2026",
                start_time="15:00",
            )

    def test_invalid_start_time_format(self):
        with pytest.raises(ValueError, match="HH:MM"):
            ParsedEvent(
                title="Test",
                start_date="2026-04-18",
                start_time="3:00 PM",
            )

    def test_confidence_clamped(self):
        event_high = ParsedEvent(
            title="Test", start_date="2026-04-18", start_time="10:00", confidence=1.5
        )
        assert event_high.confidence == 1.0

        event_low = ParsedEvent(
            title="Test", start_date="2026-04-18", start_time="10:00", confidence=-0.5
        )
        assert event_low.confidence == 0.0

    def test_missing_required_fields(self):
        with pytest.raises(Exception):
            ParsedEvent(start_date="2026-04-18", start_time="10:00")

        with pytest.raises(Exception):
            ParsedEvent(title="Test", start_time="10:00")

        with pytest.raises(Exception):
            ParsedEvent(title="Test", start_date="2026-04-18")


class TestParsedEventsList:
    def test_empty_list(self):
        events_list = ParsedEventsList()
        assert events_list.events == []

    def test_single_event(self):
        event = ParsedEvent(
            title="Meeting",
            start_date="2026-04-18",
            start_time="15:00",
            confidence=0.9,
        )
        events_list = ParsedEventsList(events=[event])
        assert len(events_list.events) == 1
        assert events_list.events[0].title == "Meeting"

    def test_multiple_events(self):
        events_list = ParsedEventsList(
            events=[
                ParsedEvent(
                    title="Бассейн",
                    start_date="2026-04-21",
                    start_time="17:00",
                    description="Солнечный город",
                    confidence=0.9,
                ),
                ParsedEvent(
                    title="Фотография",
                    start_date="2026-04-23",
                    start_time="10:00",
                    description="в садике",
                    confidence=0.9,
                ),
                ParsedEvent(
                    title="Футбол",
                    start_date="2026-04-23",
                    start_time="18:10",
                    description="Волна",
                    confidence=0.9,
                ),
            ]
        )
        assert len(events_list.events) == 3
        assert events_list.events[0].title == "Бассейн"
        assert events_list.events[1].title == "Фотография"
        assert events_list.events[2].title == "Футбол"

    def test_from_dict(self):
        data = {
            "events": [
                {
                    "title": "Meeting",
                    "start_date": "2026-04-18",
                    "start_time": "15:00",
                    "confidence": 0.9,
                }
            ]
        }
        events_list = ParsedEventsList.model_validate(data)
        assert len(events_list.events) == 1
        assert events_list.events[0].title == "Meeting"
