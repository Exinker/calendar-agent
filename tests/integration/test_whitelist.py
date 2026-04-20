"""Integration tests for whitelist functionality."""
import pytest
from datetime import datetime

from src.managers.whitelist_manager import WhitelistManager
from src.models.database_models import WhitelistUser


@pytest.mark.asyncio
async def test_add_user_to_whitelist(db_session):
    """Test adding user to whitelist."""
    manager = WhitelistManager(db_session)
    
    # Add user
    user = await manager.add_user(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        role="user"
    )
    
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    assert user.role == "user"
    assert user.is_active is True
    assert user.added_at is not None


@pytest.mark.asyncio
async def test_is_user_whitelisted(db_session):
    """Test checking if user is in whitelist."""
    manager = WhitelistManager(db_session)
    
    # User not in whitelist
    assert await manager.is_user_whitelisted(999999) is False
    
    # Add user
    await manager.add_user(telegram_id=111222333, role="user")
    
    # User should be whitelisted
    assert await manager.is_user_whitelisted(111222333) is True


@pytest.mark.asyncio
async def test_add_existing_user_reactivates(db_session):
    """Test that adding existing inactive user reactivates them."""
    manager = WhitelistManager(db_session)
    
    # Add user
    user = await manager.add_user(telegram_id=444555666, role="user")
    
    # Remove user (soft delete)
    await manager.remove_user(444555666)
    
    # Verify user is inactive
    user = await manager.get_user(444555666)
    assert user.is_active is False
    
    # Add same user again - should reactivate
    user = await manager.add_user(telegram_id=444555666, role="user")
    assert user.is_active is True


@pytest.mark.asyncio
async def test_remove_user_from_whitelist(db_session):
    """Test removing user from whitelist."""
    manager = WhitelistManager(db_session)
    
    # Add user
    await manager.add_user(telegram_id=777888999, role="user")
    
    # Verify user exists
    assert await manager.is_user_whitelisted(777888999) is True
    
    # Remove user
    success = await manager.remove_user(777888999)
    assert success is True
    
    # Verify user is removed (soft delete)
    assert await manager.is_user_whitelisted(777888999) is False


@pytest.mark.asyncio
async def test_remove_nonexistent_user(db_session):
    """Test removing user that doesn't exist."""
    manager = WhitelistManager(db_session)
    
    success = await manager.remove_user(999999999)
    assert success is False


@pytest.mark.asyncio
async def test_is_admin(db_session):
    """Test checking admin role."""
    manager = WhitelistManager(db_session)
    
    # Add regular user
    await manager.add_user(telegram_id=111111111, role="user")
    assert await manager.is_admin(111111111) is False
    
    # Add admin
    await manager.add_user(telegram_id=222222222, role="admin")
    assert await manager.is_admin(222222222) is True


@pytest.mark.asyncio
async def test_get_all_users(db_session):
    """Test getting all whitelist users."""
    manager = WhitelistManager(db_session)
    
    # Add multiple users
    await manager.add_user(telegram_id=100000001, role="user")
    await manager.add_user(telegram_id=100000002, role="user")
    await manager.add_user(telegram_id=100000003, role="admin")
    
    # Get all users
    users = await manager.get_all_users(only_active=True)
    assert len(users) == 3
    
    # Verify roles
    roles = {user.role for user in users}
    assert roles == {"user", "admin"}


@pytest.mark.asyncio
async def test_get_all_users_only_active(db_session):
    """Test that get_all_users respects only_active flag."""
    manager = WhitelistManager(db_session)
    
    # Add active user
    await manager.add_user(telegram_id=200000001, role="user")
    
    # Add and remove user
    await manager.add_user(telegram_id=200000002, role="user")
    await manager.remove_user(200000002)
    
    # Get only active users
    active_users = await manager.get_all_users(only_active=True)
    assert len(active_users) == 1
    assert active_users[0].telegram_id == 200000001
    
    # Get all users including inactive
    all_users = await manager.get_all_users(only_active=False)
    assert len(all_users) == 2


@pytest.mark.asyncio
async def test_update_last_activity(db_session):
    """Test updating last activity timestamp."""
    manager = WhitelistManager(db_session)
    
    # Add user
    user = await manager.add_user(telegram_id=300000001, role="user")
    original_activity = user.last_activity_at
    
    # Update activity
    await manager.update_last_activity(300000001)
    
    # Refresh user from DB
    updated_user = await manager.get_user(300000001)
    assert updated_user.last_activity_at > original_activity


@pytest.mark.asyncio
async def test_get_admins(db_session):
    """Test getting all admin users."""
    manager = WhitelistManager(db_session)
    
    # Add users
    await manager.add_user(telegram_id=400000001, role="user")
    await manager.add_user(telegram_id=400000002, role="admin")
    await manager.add_user(telegram_id=400000003, role="admin")
    
    # Get admins
    admins = await manager.get_admins()
    assert len(admins) == 2
    
    admin_ids = {admin.telegram_id for admin in admins}
    assert admin_ids == {400000002, 400000003}