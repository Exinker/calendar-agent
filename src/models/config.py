from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import Literal, Optional
import os


class Settings(BaseSettings):
    telegram_bot_token: str = Field(
        "", description="Telegram bot token from @BotFather"
    )
    admin_user_id: int = Field(0, description="Telegram user ID of the bot owner")

    openrouter_api_key: str = Field("", description="OpenRouter API key")
    openrouter_model: str = Field(
        "openai/gpt-3.5-turbo", description="OpenRouter model ID"
    )

    database_url: Optional[str] = Field(None, description="PostgreSQL connection URL")
    postgres_db: str = Field("calendar_bot", description="PostgreSQL database name")
    postgres_user: str = Field("bot_user", description="PostgreSQL username")
    db_password: str = Field("bot_password_123", description="PostgreSQL password")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_host: str = Field("localhost", description="PostgreSQL host")

    encryption_key: str = Field("", description="Key for encrypting calendar passwords")

    default_calendar: Literal["yandex", "icloud"] = Field(
        "yandex", description="Default calendar"
    )
    timezone: str = Field("Europe/Moscow", description="Timezone for event parsing")

    # Calendar credentials
    yandex_username: str = Field("", description="Yandex calendar username")
    yandex_app_password: str = Field("", description="Yandex calendar app password")
    icloud_username: str = Field("", description="iCloud calendar username")
    icloud_app_password: str = Field("", description="iCloud calendar app password")

    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("json", description="Log format: json or text")
    log_console: bool = Field(True, description="Enable console logging")
    log_file: bool = Field(True, description="Enable file logging")
    log_file_path: str = Field("logs/bot.log", description="Path to log file")
    log_rotation_size: str = Field("10MB", description="Max size before rotation")
    log_backup_count: int = Field(5, description="Number of backup files to keep")

    @model_validator(mode="before")
    @classmethod
    def build_database_url(cls, values: dict) -> dict:
        """Build DATABASE_URL from individual postgres params if not provided."""
        if not values.get("database_url"):
            db = values.get("postgres_db", "calendar_bot")
            user = values.get("postgres_user", "bot_user")
            pwd = values.get("db_password", "bot_password_123")
            host = values.get("postgres_host", "localhost")
            port = values.get("postgres_port", 5432)
            values["database_url"] = (
                f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"
            )
        return values

    @field_validator("telegram_bot_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if v and ":" not in v:
            raise ValueError("Invalid Telegram bot token format")
        return v

    @field_validator("admin_user_id")
    @classmethod
    def validate_admin_id(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Admin user ID must be non-negative")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
