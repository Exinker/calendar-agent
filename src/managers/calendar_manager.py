"""Calendar manager for working with calendar credentials and clients."""
import logging
from typing import Optional
from sqlalchemy import select

from src.models.database_models import CalendarConfig
from src.services.calendar.yandex import YandexCalendarClient
from src.services.calendar.icloud import ICloudCalendarClient
from src.services.calendar.base import BaseCalendarClient
from src.utils.encryption import decrypt_password

logger = logging.getLogger(__name__)


class CalendarManager:
    """Manages calendar configurations and provides calendar clients."""
    
    def __init__(self, db_session):
        self.db = db_session
        self._active_config = None
        self._client = None
    
    async def get_active_calendar_config(self) -> Optional[CalendarConfig]:
        """Get currently active calendar configuration."""
        if self._active_config is None:
            # Query database for active calendar
            result = await self.db.execute(
                select(CalendarConfig).where(CalendarConfig.is_active == True).limit(1)
            )
            self._active_config = result.scalar_one_or_none()
        return self._active_config
    
    async def get_calendar_client(self) -> Optional[BaseCalendarClient]:
        """Get calendar client with current credentials."""
        if self._client is None:
            config = await self.get_active_calendar_config()
            if not config:
                logger.warning("No active calendar configuration found")
                return None
            
            try:
                # Decrypt password
                password = decrypt_password(config.encrypted_password)
                
                # Create appropriate client
                if config.calendar_type == "yandex":
                    self._client = YandexCalendarClient(
                        username=config.username,
                        password=password
                    )
                elif config.calendar_type == "icloud":
                    self._client = ICloudCalendarClient(
                        username=config.username,
                        password=password
                    )
                else:
                    logger.error(f"Unknown calendar type: {config.calendar_type}")
                    return None
                
                logger.info(f"Created {config.calendar_type} calendar client for {config.username}")
            except Exception as e:
                logger.error(f"Failed to create calendar client: {e}")
                return None
        
        return self._client
    
    async def invalidate_cache(self):
        """Invalidate cached client and config."""
        self._active_config = None
        self._client = None
        logger.info("Calendar manager cache invalidated")