"""Integration tests for calendar service scenarios."""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_create_event_logs_to_database(db_session, test_encryption_key):
    """Scenario: Creating event logs it to database with user attribution."""
    from src.managers.event_logger import EventLogger
    
    logger = EventLogger(db_session)
    
    # Log an event
    await logger.log_event(
        telegram_user_id=123456789,
        event_title="Test Meeting",
        event_date=datetime(2024, 5, 20, 14, 0),
        calendar_type="yandex",
        event_description="Test description"
    )
    
    # Verify event was logged
    from sqlalchemy import select
    from src.models.database_models import EventLog
    
    result = await db_session.execute(
        select(EventLog).where(EventLog.telegram_user_id == 123456789)
    )
    events = result.scalars().all()
    
    assert len(events) == 1
    assert events[0].event_title == "Test Meeting"
    assert events[0].calendar_type == "yandex"


@pytest.mark.asyncio
async def test_user_stats_tracked_correctly(db_session):
    """Scenario: User stats are updated when events are created."""
    from src.managers.event_logger import EventLogger
    
    logger = EventLogger(db_session)
    user_id = 234567890
    
    # Create multiple events
    for i in range(3):
        await logger.log_event(
            telegram_user_id=user_id,
            event_title=f"Event {i}",
            event_date=datetime(2024, 5, 20, 14, 0),
            calendar_type="yandex"
        )
    
    # Check stats
    stats = await logger.get_user_stats(user_id)
    assert stats is not None
    assert stats.events_created == 3
    assert stats.last_event_at is not None


@pytest.mark.asyncio
async def test_multiple_users_have_separate_stats(db_session):
    """Scenario: Different users have separate event statistics."""
    from src.managers.event_logger import EventLogger
    
    logger = EventLogger(db_session)
    
    # User 1 creates 2 events
    for i in range(2):
        await logger.log_event(
            telegram_user_id=111111111,
            event_title=f"User1 Event {i}",
            event_date=datetime(2024, 5, 20, 14, 0),
            calendar_type="yandex"
        )
    
    # User 2 creates 1 event
    await logger.log_event(
        telegram_user_id=222222222,
        event_title="User2 Event",
        event_date=datetime(2024, 5, 20, 15, 0),
        calendar_type="icloud"
    )
    
    # Verify separate stats
    stats1 = await logger.get_user_stats(111111111)
    stats2 = await logger.get_user_stats(222222222)
    
    assert stats1.events_created == 2
    assert stats2.events_created == 1


@pytest.mark.asyncio
async def test_get_recent_events_limited(db_session):
    """Scenario: Getting recent events returns limited number."""
    from src.managers.event_logger import EventLogger
    
    logger = EventLogger(db_session)
    
    # Create 5 events
    for i in range(5):
        await logger.log_event(
            telegram_user_id=333333333,
            event_title=f"Event {i}",
            event_date=datetime(2024, 5, 20, 14, 0),
            calendar_type="yandex"
        )
    
    # Get only 3 recent
    recent = await logger.get_recent_events(limit=3)
    assert len(recent) == 3


@pytest.mark.asyncio
async def test_get_recent_events_filtered_by_user(db_session):
    """Scenario: Getting recent events can be filtered by user."""
    from src.managers.event_logger import EventLogger
    
    logger = EventLogger(db_session)
    
    # User 1 events
    await logger.log_event(
        telegram_user_id=444444444,
        event_title="User1 Event",
        event_date=datetime(2024, 5, 20, 14, 0),
        calendar_type="yandex"
    )
    
    # User 2 events
    await logger.log_event(
        telegram_user_id=555555555,
        event_title="User2 Event",
        event_date=datetime(2024, 5, 20, 15, 0),
        calendar_type="yandex"
    )
    
    # Get only user 1 events
    user1_events = await logger.get_recent_events(
        telegram_user_id=444444444,
        limit=10
    )
    
    assert len(user1_events) == 1
    assert user1_events[0].event_title == "User1 Event"


@pytest.mark.asyncio
async def test_event_calendar_type_preserved(db_session):
    """Scenario: Calendar type (yandex/icloud) is preserved in logs."""
    from src.managers.event_logger import EventLogger
    
    logger = EventLogger(db_session)
    
    # Log events with different calendar types
    await logger.log_event(
        telegram_user_id=666666666,
        event_title="Yandex Event",
        event_date=datetime(2024, 5, 20, 14, 0),
        calendar_type="yandex"
    )
    
    await logger.log_event(
        telegram_user_id=666666666,
        event_title="iCloud Event",
        event_date=datetime(2024, 5, 20, 15, 0),
        calendar_type="icloud"
    )
    
    # Verify types preserved
    events = await logger.get_recent_events(telegram_user_id=666666666, limit=10)
    calendar_types = {e.calendar_type for e in events}
    
    assert calendar_types == {"yandex", "icloud"}