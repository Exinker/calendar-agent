"""Whitelist manager for user access control."""
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database_models import WhitelistUser

logger = logging.getLogger(__name__)


class WhitelistManager:
    """Manages whitelist users and access control."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def is_user_whitelisted(self, telegram_id: int) -> bool:
        """Check if user is in whitelist."""
        result = await self.db.execute(
            select(WhitelistUser).where(
                WhitelistUser.telegram_id == telegram_id,
                WhitelistUser.is_active == True
            )
        )
        user = result.scalar_one_or_none()
        return user is not None
    
    async def get_user(self, telegram_id: int) -> Optional[WhitelistUser]:
        """Get user by telegram_id."""
        result = await self.db.execute(
            select(WhitelistUser).where(WhitelistUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def add_user(
        self, 
        telegram_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "user",
        added_by: Optional[int] = None
    ) -> WhitelistUser:
        """Add user to whitelist."""
        # Check if user already exists
        existing = await self.get_user(telegram_id)
        if existing:
            if existing.is_active:
                logger.warning(f"User {telegram_id} already in whitelist")
                return existing
            # Reactivate user
            existing.is_active = True
            existing.role = role
            await self.db.commit()
            logger.info(f"Reactivated user {telegram_id}")
            return existing
        
        # Create new user
        user = WhitelistUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            added_by_telegram_id=added_by,
            added_at=datetime.utcnow(),
            is_active=True
        )
        self.db.add(user)
        await self.db.commit()
        logger.info(f"Added user {telegram_id} to whitelist with role {role}")
        return user
    
    async def remove_user(self, telegram_id: int) -> bool:
        """Remove user from whitelist (soft delete)."""
        user = await self.get_user(telegram_id)
        if not user:
            logger.warning(f"User {telegram_id} not found in whitelist")
            return False
        
        user.is_active = False
        await self.db.commit()
        logger.info(f"Removed user {telegram_id} from whitelist")
        return True
    
    async def update_last_activity(self, telegram_id: int):
        """Update user's last activity timestamp."""
        await self.db.execute(
            update(WhitelistUser)
            .where(WhitelistUser.telegram_id == telegram_id)
            .values(last_activity_at=datetime.utcnow())
        )
        await self.db.commit()
    
    async def get_all_users(self, only_active: bool = True) -> List[WhitelistUser]:
        """Get all whitelist users."""
        query = select(WhitelistUser)
        if only_active:
            query = query.where(WhitelistUser.is_active == True)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_admins(self) -> List[WhitelistUser]:
        """Get all admin users."""
        result = await self.db.execute(
            select(WhitelistUser).where(
                WhitelistUser.role == "admin",
                WhitelistUser.is_active == True
            )
        )
        return result.scalars().all()
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin."""
        user = await self.get_user(telegram_id)
        return user is not None and user.role == "admin" and user.is_active