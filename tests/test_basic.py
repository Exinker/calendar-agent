"""Basic smoke tests without Docker dependency."""
import pytest
import os


@pytest.fixture(scope="module")
def encryption_key():
    """Set up test encryption key."""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = key
    return key


@pytest.fixture(scope="module")
def env_setup():
    """Set up minimal environment for imports."""
    os.environ["TELEGRAM_BOT_TOKEN"] = "test:token"
    os.environ["ADMIN_USER_ID"] = "123456789"
    os.environ["OPENROUTER_API_KEY"] = "test_key"
    os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost/test"
    os.environ["DEFAULT_CALENDAR"] = "yandex"
    os.environ["TIMEZONE"] = "Europe/Moscow"
    
    from cryptography.fernet import Fernet
    os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()


def test_encryption_roundtrip(encryption_key):
    """Test that password can be encrypted and decrypted."""
    from src.utils.encryption import encrypt_password, decrypt_password
    
    original_password = "my_secret_password_123"
    encrypted = encrypt_password(original_password)
    decrypted = decrypt_password(encrypted)
    
    assert encrypted != original_password
    assert decrypted == original_password


def test_different_passwords_different_encryption(encryption_key):
    """Test that different passwords produce different encrypted values."""
    from src.utils.encryption import encrypt_password
    
    password1 = "password123"
    password2 = "password456"
    
    encrypted1 = encrypt_password(password1)
    encrypted2 = encrypt_password(password2)
    
    assert encrypted1 != encrypted2


def test_models_import(env_setup):
    """Test that all models can be imported."""
    from src.models.database_models import WhitelistUser, CalendarConfig, EventLog, UsageStats
    from src.models.domain import ParsedEvent, ParsedEventsList
    from src.models.config import Settings
    
    assert WhitelistUser is not None
    assert CalendarConfig is not None
    assert EventLog is not None
    assert UsageStats is not None
    assert ParsedEvent is not None
    assert ParsedEventsList is not None
    assert Settings is not None


def test_managers_import(env_setup):
    """Test that all managers can be imported."""
    from src.managers.whitelist_manager import WhitelistManager
    from src.managers.calendar_manager import CalendarManager
    from src.managers.event_logger import EventLogger
    
    assert WhitelistManager is not None
    assert CalendarManager is not None
    assert EventLogger is not None


def test_services_import(env_setup):
    """Test that all services can be imported."""
    from src.services.calendar.yandex import YandexCalendarClient
    from src.services.calendar.icloud import ICloudCalendarClient
    from src.services.calendar.base import BaseCalendarClient
    from src.services.llm_service import parse_events_with_llm
    
    assert YandexCalendarClient is not None
    assert ICloudCalendarClient is not None
    assert BaseCalendarClient is not None
    assert parse_events_with_llm is not None