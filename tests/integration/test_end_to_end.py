"""End-to-end integration tests for complete user workflows."""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_complete_admin_workflow(db_session, test_encryption_key):
    """Scenario: Admin sets up bot, adds user, user creates event."""
    from src.managers.whitelist_manager import WhitelistManager
    from src.managers.event_logger import EventLogger
    from src.managers.calendar_manager import CalendarManager
    from src.models.database_models import CalendarConfig
    from src.utils.encryption import encrypt_password
    from sqlalchemy import select
    
    # Step 1: Setup - Create admin
    whitelist_mgr = WhitelistManager(db_session)
    admin_id = 100000001
    await whitelist_mgr.add_user(telegram_id=admin_id, role="admin")
    
    # Step 2: Setup - Configure calendar
    calendar_config = CalendarConfig(
        calendar_type="yandex",
        username="family@yandex.ru",
        encrypted_password=encrypt_password("app_password_123"),
        is_active=True,
        is_default=True
    )
    db_session.add(calendar_config)
    await db_session.commit()
    
    # Step 3: Admin adds regular user
    user_id = 100000002
    await whitelist_mgr.add_user(
        telegram_id=user_id,
        username="family_member",
        added_by=admin_id
    )
    
    # Step 4: Verify user can access
    assert await whitelist_mgr.is_user_whitelisted(user_id) is True
    
    # Step 5: User creates event (simulated)
    event_logger = EventLogger(db_session)
    await event_logger.log_event(
        telegram_user_id=user_id,
        event_title="Family Dinner",
        event_date=datetime(2024, 5, 25, 19, 0),
        calendar_type="yandex",
        event_description="Weekly family dinner"
    )
    
    # Step 6: Verify event logged
    stats = await event_logger.get_user_stats(user_id)
    assert stats.events_created == 1
    
    # Step 7: Verify admin can see all users
    all_users = await whitelist_mgr.get_all_users()
    assert len(all_users) == 2  # admin + user


@pytest.mark.asyncio
async def test_multiple_users_same_calendar(db_session, test_encryption_key):
    """Scenario: Multiple users share same calendar and add events."""
    from src.managers.whitelist_manager import WhitelistManager
    from src.managers.event_logger import EventLogger
    from src.models.database_models import CalendarConfig
    from src.utils.encryption import encrypt_password
    
    # Setup: Create shared calendar
    calendar_config = CalendarConfig(
        calendar_type="icloud",
        username="family@icloud.com",
        encrypted_password=encrypt_password("shared_password"),
        is_active=True
    )
    db_session.add(calendar_config)
    await db_session.commit()
    
    # Setup: Add multiple users
    whitelist_mgr = WhitelistManager(db_session)
    user_ids = [200000001, 200000002, 200000003]
    
    for uid in user_ids:
        await whitelist_mgr.add_user(telegram_id=uid, role="user")
    
    # Each user creates events
    event_logger = EventLogger(db_session)
    for i, uid in enumerate(user_ids):
        await event_logger.log_event(
            telegram_user_id=uid,
            event_title=f"Event from user {i}",
            event_date=datetime(2024, 5, 20 + i, 14, 0),
            calendar_type="icloud"
        )
    
    # Verify all events logged
    all_events = await event_logger.get_recent_events(limit=10)
    assert len(all_events) == 3
    
    # Verify each user's stats
    for uid in user_ids:
        stats = await event_logger.get_user_stats(uid)
        assert stats.events_created == 1


@pytest.mark.asyncio
async def test_user_removed_mid_usage(db_session, test_encryption_key):
    """Scenario: User is removed while having existing events."""
    from src.managers.whitelist_manager import WhitelistManager
    from src.managers.event_logger import EventLogger
    
    whitelist_mgr = WhitelistManager(db_session)
    event_logger = EventLogger(db_session)
    
    # Setup: Add user
    user_id = 300000001
    await whitelist_mgr.add_user(telegram_id=user_id, role="user")
    
    # User creates some events
    for i in range(3):
        await event_logger.log_event(
            telegram_user_id=user_id,
            event_title=f"Event {i}",
            event_date=datetime(2024, 5, 20, 14, 0),
            calendar_type="yandex"
        )
    
    # Verify events exist
    stats = await event_logger.get_user_stats(user_id)
    assert stats.events_created == 3
    
    # Admin removes user
    await whitelist_mgr.remove_user(user_id)
    
    # Verify user lost access
    assert await whitelist_mgr.is_user_whitelisted(user_id) is False
    
    # But events are still in log (for audit)
    events = await event_logger.get_recent_events(telegram_user_id=user_id, limit=10)
    assert len(events) == 3


@pytest.mark.asyncio
async def test_statistics_accuracy(db_session, test_encryption_key):
    """Scenario: Statistics accurately reflect user activity."""
    from src.managers.whitelist_manager import WhitelistManager
    from src.managers.event_logger import EventLogger
    
    whitelist_mgr = WhitelistManager(db_session)
    event_logger = EventLogger(db_session)
    
    # Add active and inactive users
    active_user = 400000001
    inactive_user = 400000002
    
    await whitelist_mgr.add_user(telegram_id=active_user, role="user")
    await whitelist_mgr.add_user(telegram_id=inactive_user, role="user")
    
    # Only active user creates events
    for i in range(5):
        await event_logger.log_event(
            telegram_user_id=active_user,
            event_title=f"Active Event {i}",
            event_date=datetime(2024, 5, 20, 14, 0),
            calendar_type="yandex"
        )
    
    # Remove inactive user
    await whitelist_mgr.remove_user(inactive_user)
    
    # Get stats
    active_stats = await event_logger.get_user_stats(active_user)
    inactive_stats = await event_logger.get_user_stats(inactive_user)
    
    # Verify
    assert active_stats.events_created == 5
    assert inactive_stats is None  # Never created events
    
    # Verify only active users in whitelist
    active_users = await whitelist_mgr.get_all_users(only_active=True)
    assert len(active_users) == 1
    assert active_users[0].telegram_id == active_user


@pytest.mark.asyncio
async def test_audit_trail(db_session, test_encryption_key):
    """Scenario: Complete audit trail of who added what."""
    from src.managers.whitelist_manager import WhitelistManager
    from src.managers.event_logger import EventLogger
    from src.models.database_models import EventLog
    from sqlalchemy import select
    
    whitelist_mgr = WhitelistManager(db_session)
    event_logger = EventLogger(db_session)
    
    # Admin adds two users
    admin_id = 500000001
    user1_id = 500000002
    user2_id = 500000003
    
    await whitelist_mgr.add_user(telegram_id=admin_id, role="admin")
    await whitelist_mgr.add_user(telegram_id=user1_id, role="user", added_by=admin_id)
    await whitelist_mgr.add_user(telegram_id=user2_id, role="user", added_by=admin_id)
    
    # Users create events
    await event_logger.log_event(
        telegram_user_id=user1_id,
        event_title="User1 Meeting",
        event_date=datetime(2024, 5, 20, 10, 0),
        calendar_type="yandex"
    )
    
    await event_logger.log_event(
        telegram_user_id=user2_id,
        event_title="User2 Appointment",
        event_date=datetime(2024, 5, 20, 14, 0),
        calendar_type="icloud"
    )
    
    # Verify audit trail
    result = await db_session.execute(select(EventLog))
    all_events = result.scalars().all()
    
    assert len(all_events) == 2
    
    # Verify attribution
    event_owners = {e.telegram_user_id for e in all_events}
    assert event_owners == {user1_id, user2_id}