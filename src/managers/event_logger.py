"""Event logging manager."""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database_models import EventLog, UsageStats

logger = logging.getLogger(__name__)


class EventLogger:
    """Logs calendar events and user activity."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def log_event(
        self,
        telegram_user_id: int,
        event_title: str,
        event_date: datetime,
        calendar_type: str,
        event_description: Optional[str] = None,
        action: str = "created"
    ):
        """Log created event to database."""
        try:
            # Create event log entry
            log_entry = EventLog(
                telegram_user_id=telegram_user_id,
                event_title=event_title,
                event_date=event_date,
                event_description=event_description,
                calendar_type=calendar_type,
                action=action,
                created_at=datetime.utcnow()
            )
            self.db.add(log_entry)
            
            # Update usage stats
            stats = await self.db.get(UsageStats, telegram_user_id)
            if stats:
                stats.events_created += 1
                stats.last_event_at = datetime.utcnow()
            else:
                stats = UsageStats(
                    telegram_user_id=telegram_user_id,
                    events_created=1,
                    last_event_at=datetime.utcnow(),
                    first_event_at=datetime.utcnow()
                )
                self.db.add(stats)
            
            await self.db.commit()
            logger.info(f"Logged event '{event_title}' for user {telegram_user_id}")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            await self.db.rollback()
            raise
    
    async def get_user_stats(self, telegram_user_id: int) -> Optional[UsageStats]:
        """Get usage statistics for a user."""
        return await self.db.get(UsageStats, telegram_user_id)
    
    async def get_recent_events(
        self, 
        telegram_user_id: Optional[int] = None,
        limit: int = 10
    ):
        """Get recent events (optionally filtered by user)."""
        from sqlalchemy import select, desc
        
        query = select(EventLog).order_by(desc(EventLog.created_at)).limit(limit)
        if telegram_user_id:
            query = query.where(EventLog.telegram_user_id == telegram_user_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()