"""Integration tests for calendar service scenarios."""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_password_encryption_roundtrip(test_encryption_key):
    """Scenario: Password can be encrypted and decrypted back."""
    from src.utils.encryption import encrypt_password, decrypt_password
    
    original_password = "my_secret_password_123"
    
    # Encrypt
    encrypted = encrypt_password(original_password)
    assert encrypted != original_password
    assert isinstance(encrypted, str)
    
    # Decrypt
    decrypted = decrypt_password(encrypted)
    assert decrypted == original_password


@pytest.mark.asyncio
async def test_different_passwords_produce_different_encryptions(test_encryption_key):
    """Scenario: Different passwords produce different encrypted values."""
    from src.utils.encryption import encrypt_password
    
    password1 = "password123"
    password2 = "password456"
    
    encrypted1 = encrypt_password(password1)
    encrypted2 = encrypt_password(password2)
    
    assert encrypted1 != encrypted2


@pytest.mark.asyncio
async def test_calendar_config_can_be_stored_encrypted(db_session, test_encryption_key):
    """Scenario: Calendar credentials are stored encrypted in database."""
    from src.utils.encryption import encrypt_password
    from src.models.database_models import CalendarConfig
    
    # Store encrypted password
    password = "yandex_app_password"
    encrypted = encrypt_password(password)
    
    config = CalendarConfig(
        calendar_type="yandex",
        username="test@yandex.ru",
        encrypted_password=encrypted,
        is_active=True
    )
    
    db_session.add(config)
    await db_session.commit()
    
    # Retrieve and verify it's encrypted
    from sqlalchemy import select
    result = await db_session.execute(
        select(CalendarConfig).where(CalendarConfig.username == "test@yandex.ru")
    )
    stored_config = result.scalar_one()
    
    assert stored_config.encrypted_password != password
    assert stored_config.encrypted_password == encrypted


@pytest.mark.asyncio
async def test_calendar_config_can_be_decrypted(db_session, test_encryption_key):
    """Scenario: Stored calendar credentials can be decrypted for use."""
    from src.utils.encryption import encrypt_password, decrypt_password
    from src.models.database_models import CalendarConfig
    
    # Store encrypted
    original_password = "icloud_app_password"
    encrypted = encrypt_password(original_password)
    
    config = CalendarConfig(
        calendar_type="icloud",
        username="test@icloud.com",
        encrypted_password=encrypted,
        is_active=True
    )
    
    db_session.add(config)
    await db_session.commit()
    
    # Retrieve and decrypt
    from sqlalchemy import select
    result = await db_session.execute(
        select(CalendarConfig).where(CalendarConfig.username == "test@icloud.com")
    )
    stored_config = result.scalar_one()
    
    decrypted = decrypt_password(stored_config.encrypted_password)
    assert decrypted == original_password


@pytest.mark.asyncio
async def test_multiple_calendar_configs_can_exist(db_session, test_encryption_key):
    """Scenario: Multiple calendar configurations can be stored."""
    from src.utils.encryption import encrypt_password
    from src.models.database_models import CalendarConfig
    
    # Add Yandex config
    yandex_config = CalendarConfig(
        calendar_type="yandex",
        username="yandex@yandex.ru",
        encrypted_password=encrypt_password("yandex_pass"),
        is_active=True
    )
    
    # Add iCloud config
    icloud_config = CalendarConfig(
        calendar_type="icloud",
        username="icloud@icloud.com",
        encrypted_password=encrypt_password("icloud_pass"),
        is_active=True
    )
    
    db_session.add_all([yandex_config, icloud_config])
    await db_session.commit()
    
    # Verify both exist
    from sqlalchemy import select
    result = await db_session.execute(select(CalendarConfig))
    configs = result.scalars().all()
    
    assert len(configs) == 2
    calendar_types = {c.calendar_type for c in configs}
    assert calendar_types == {"yandex", "icloud"}


@pytest.mark.asyncio
async def test_only_active_calendar_configs_are_used(db_session, test_encryption_key):
    """Scenario: Only active calendar configs should be used by manager."""
    from src.utils.encryption import encrypt_password
    from src.models.database_models import CalendarConfig
    from sqlalchemy import select
    
    # Add active config
    active_config = CalendarConfig(
        calendar_type="yandex",
        username="active@yandex.ru",
        encrypted_password=encrypt_password("active_pass"),
        is_active=True
    )
    
    # Add inactive config
    inactive_config = CalendarConfig(
        calendar_type="icloud",
        username="inactive@icloud.com",
        encrypted_password=encrypt_password("inactive_pass"),
        is_active=False
    )
    
    db_session.add_all([active_config, inactive_config])
    await db_session.commit()
    
    # Get only active configs
    result = await db_session.execute(
        select(CalendarConfig).where(CalendarConfig.is_active == True)
    )
    active_configs = result.scalars().all()
    
    assert len(active_configs) == 1
    assert active_configs[0].username == "active@yandex.ru"