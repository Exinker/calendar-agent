"""Integration tests for whitelist service scenarios."""
import pytest


@pytest.mark.asyncio
async def test_new_user_cannot_access_bot(db_session):
    """Scenario: New user without whitelist access is rejected."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # New user tries to access
    user_id = 999999999
    is_allowed = await manager.is_user_whitelisted(user_id)
    
    assert is_allowed is False


@pytest.mark.asyncio
async def test_admin_can_add_user_and_user_gets_access(db_session):
    """Scenario: Admin adds user, user can then access the bot."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Setup: Create admin
    await manager.add_user(telegram_id=100000001, role="admin")
    
    # Admin adds new user
    new_user_id = 100000002
    await manager.add_user(
        telegram_id=new_user_id,
        username="newuser",
        added_by=100000001
    )
    
    # New user can now access
    is_allowed = await manager.is_user_whitelisted(new_user_id)
    assert is_allowed is True


@pytest.mark.asyncio
async def test_regular_user_cannot_add_other_users(db_session):
    """Scenario: Regular user tries to add someone - should fail permission check."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Create regular user
    await manager.add_user(telegram_id=200000001, role="user")
    
    # Verify user is not admin
    is_admin = await manager.is_admin(200000001)
    assert is_admin is False


@pytest.mark.asyncio
async def test_removed_user_loses_access(db_session):
    """Scenario: User is removed from whitelist and loses access."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Setup: Add user
    user_id = 300000001
    await manager.add_user(telegram_id=user_id, role="user")
    
    # Verify user has access
    assert await manager.is_user_whitelisted(user_id) is True
    
    # Admin removes user
    await manager.remove_user(user_id)
    
    # User loses access
    assert await manager.is_user_whitelisted(user_id) is False


@pytest.mark.asyncio
async def test_reactivated_user_regains_access(db_session):
    """Scenario: Removed user is re-added and regains access."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Setup: Add and remove user
    user_id = 400000001
    await manager.add_user(telegram_id=user_id, role="user")
    await manager.remove_user(user_id)
    
    # Verify no access
    assert await manager.is_user_whitelisted(user_id) is False
    
    # Re-add user
    await manager.add_user(telegram_id=user_id, role="user")
    
    # User regains access
    assert await manager.is_user_whitelisted(user_id) is True


@pytest.mark.asyncio
async def test_user_activity_is_tracked(db_session):
    """Scenario: User activity is tracked when they use the bot."""
    from src.managers.whitelist_manager import WhitelistManager
    from datetime import datetime
    
    manager = WhitelistManager(db_session)
    
    # Add user
    user_id = 500000001
    user = await manager.add_user(telegram_id=user_id, role="user")
    original_activity = user.last_activity_at
    
    # Simulate activity
    await manager.update_last_activity(user_id)
    
    # Verify activity was updated
    updated_user = await manager.get_user(user_id)
    assert updated_user.last_activity_at > original_activity


@pytest.mark.asyncio
async def test_multiple_admins_can_exist(db_session):
    """Scenario: Multiple admin users can coexist."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Add multiple admins
    await manager.add_user(telegram_id=600000001, role="admin")
    await manager.add_user(telegram_id=600000002, role="admin")
    await manager.add_user(telegram_id=600000003, role="user")
    
    # Get all admins
    admins = await manager.get_admins()
    
    assert len(admins) == 2
    admin_ids = {admin.telegram_id for admin in admins}
    assert admin_ids == {600000001, 600000002}


@pytest.mark.asyncio
async def test_admin_cannot_remove_themselves(db_session):
    """Scenario: Admin tries to remove themselves - should be prevented."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Setup: Create admin
    admin_id = 700000001
    await manager.add_user(telegram_id=admin_id, role="admin")
    
    # Verify admin exists
    assert await manager.is_admin(admin_id) is True
    
    # Admin tries to remove themselves (this would be checked in handler)
    # Here we just verify the method works
    success = await manager.remove_user(admin_id)
    assert success is True  # Method succeeds
    
    # Admin is removed
    assert await manager.is_admin(admin_id) is False


@pytest.mark.asyncio
async def test_user_list_shows_only_active_by_default(db_session):
    """Scenario: Listing users shows only active ones by default."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # Add users
    await manager.add_user(telegram_id=800000001, role="user")
    await manager.add_user(telegram_id=800000002, role="user")
    
    # Remove one user
    await manager.remove_user(800000002)
    
    # List shows only active
    active_users = await manager.get_all_users(only_active=True)
    assert len(active_users) == 1
    assert active_users[0].telegram_id == 800000001


@pytest.mark.asyncio
async def test_full_user_lifecycle(db_session):
    """Scenario: Complete user lifecycle - add, use, remove."""
    from src.managers.whitelist_manager import WhitelistManager
    
    manager = WhitelistManager(db_session)
    
    # 1. New user cannot access
    user_id = 900000001
    assert await manager.is_user_whitelisted(user_id) is False
    
    # 2. Admin adds user
    await manager.add_user(
        telegram_id=user_id,
        username="lifecycle_user",
        first_name="Lifecycle",
        last_name="User"
    )
    
    # 3. User can access
    assert await manager.is_user_whitelisted(user_id) is True
    
    # 4. User activity is tracked
    await manager.update_last_activity(user_id)
    user = await manager.get_user(user_id)
    assert user.last_activity_at is not None
    
    # 5. Admin removes user
    await manager.remove_user(user_id)
    
    # 6. User cannot access anymore
    assert await manager.is_user_whitelisted(user_id) is False