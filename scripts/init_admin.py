"""Initialize first admin user and calendar configuration."""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from src.dao.database import AsyncSessionLocal, engine
from src.models.database_models import Base, WhitelistUser, CalendarConfig
from src.utils.encryption import encrypt_password


class InitSettings(BaseSettings):
    """Settings for initialization script."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    admin_user_id: int
    default_calendar: str = "yandex"
    yandex_username: str = ""
    yandex_app_password: str = ""
    icloud_username: str = ""
    icloud_app_password: str = ""


# Load settings from .env
init_settings = InitSettings()


async def init_admin():
    """Initialize admin user from environment variables."""
    admin_id = init_settings.admin_user_id

    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        existing = await session.get(WhitelistUser, admin_id)
        if existing:
            print(f"Admin user {admin_id} already exists")
            return

        # Create admin user
        admin = WhitelistUser(
            telegram_id=admin_id,
            role="admin",
            added_at=datetime.utcnow(),
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"✅ Admin user {admin_id} created successfully")


async def init_calendar():
    """Initialize calendar configuration from environment variables."""
    calendar_type = init_settings.default_calendar

    if calendar_type == "yandex":
        username = init_settings.yandex_username
        password = init_settings.yandex_app_password
    elif calendar_type == "icloud":
        username = init_settings.icloud_username
        password = init_settings.icloud_app_password
    else:
        print(
            f"Warning: Unknown calendar type '{calendar_type}', skipping calendar init"
        )
        return

    if not username or not password:
        print(f"Warning: Calendar credentials not found for {calendar_type}")
        print("You can configure calendar later via database")
        return

    async with AsyncSessionLocal() as session:
        # Check if calendar already configured
        from sqlalchemy import select

        result = await session.execute(
            select(CalendarConfig).where(CalendarConfig.is_active == True)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Calendar already configured: {existing.calendar_type}")
            return

        # Encrypt password
        encrypted_password = encrypt_password(password)

        # Create calendar config
        config = CalendarConfig(
            calendar_type=calendar_type,
            username=username,
            encrypted_password=encrypted_password,
            is_active=True,
            is_default=True,
        )
        session.add(config)
        await session.commit()
        print(f"✅ {calendar_type.title()} calendar configured for {username}")


async def main():
    """Main initialization function."""
    print("🚀 Initializing Calendar Bot...")

    # Create tables if not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    # Initialize admin
    await init_admin()

    # Initialize calendar
    await init_calendar()

    print("\n🎉 Initialization complete!")
    print("You can now start the bot with: make run")


if __name__ == "__main__":
    asyncio.run(main())
