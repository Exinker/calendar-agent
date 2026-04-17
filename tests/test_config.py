import pytest
from config import Settings


class TestConfig:
    def test_settings_load_from_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        monkeypatch.setenv("ADMIN_USER_ID", "123456789")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("TIMEZONE", "Europe/Moscow")

        s = Settings()
        assert s.telegram_bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert s.admin_user_id == 123456789
        assert s.openrouter_api_key == "test-key"
        assert s.default_calendar == "yandex"
        assert s.timezone == "Europe/Moscow"

    def test_invalid_telegram_token(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "invalid")
        monkeypatch.setenv("ADMIN_USER_ID", "123456789")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        with pytest.raises(Exception):
            Settings()

    def test_invalid_admin_id(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        monkeypatch.setenv("ADMIN_USER_ID", "-1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        with pytest.raises(Exception):
            Settings()

    def test_default_calendar_validation(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        monkeypatch.setenv("ADMIN_USER_ID", "123456789")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("DEFAULT_CALENDAR", "icloud")

        s = Settings()
        assert s.default_calendar == "icloud"
