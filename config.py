from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., description="Telegram bot token from @BotFather")
    admin_user_id: int = Field(..., description="Telegram user ID of the bot owner")

    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_model: str = Field("openai/gpt-3.5-turbo", description="OpenRouter model ID")

    yandex_enabled: bool = Field(True, description="Enable Yandex Calendar")
    yandex_username: Optional[str] = Field(None, description="Yandex login")
    yandex_app_password: Optional[str] = Field(None, description="Yandex app-specific password")

    icloud_enabled: bool = Field(True, description="Enable iCloud Calendar")
    icloud_username: Optional[str] = Field(None, description="Apple ID email")
    icloud_app_password: Optional[str] = Field(None, description="iCloud app-specific password")

    default_calendar: Literal["yandex", "icloud"] = Field("yandex", description="Default calendar")
    timezone: str = Field("Europe/Moscow", description="Timezone for event parsing")

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

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
