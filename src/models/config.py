from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    telegram_bot_token: str = Field(
        ..., description="Telegram bot token from @BotFather"
    )
    admin_user_id: int = Field(..., description="Telegram user ID of the bot owner")

    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_model: str = Field(
        "openai/gpt-3.5-turbo", description="OpenRouter model ID"
    )

    database_url: str = Field(
        "postgresql+psycopg://bot_user:bot_password_123@localhost:5432/calendar_bot",
        description="PostgreSQL connection URL",
    )
    encryption_key: str = Field(
        ..., description="Key for encrypting calendar passwords"
    )

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

    @field_validator("telegram_bot_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or ":" not in v:
            raise ValueError("Invalid Telegram bot token format")
        return v

    @field_validator("admin_user_id")
    @classmethod
    def validate_admin_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Admin user ID must be positive")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
