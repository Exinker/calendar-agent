from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, BigInteger
from sqlalchemy.sql import func

from src.dao.database import Base


class WhitelistUser(Base):
    """Пользователи с доступом к календарю"""
    __tablename__ = "whitelist_users"
    
    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # admin, user
    added_by_telegram_id = Column(BigInteger, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class CalendarConfig(Base):
    """Настройки календарей (один активный календарь)"""
    __tablename__ = "calendar_config"
    
    id = Column(Integer, primary_key=True)
    calendar_type = Column(String(20), nullable=False)  # yandex, icloud
    calendar_name = Column(String(100), nullable=True)
    username = Column(String(100), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EventLog(Base):
    """Журнал добавленных событий"""
    __tablename__ = "event_log"
    
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, nullable=False)
    event_title = Column(String(200), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    event_description = Column(Text, nullable=True)
    calendar_type = Column(String(20), nullable=False)
    action = Column(String(20), default="created", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UsageStats(Base):
    """Статистика использования по пользователям"""
    __tablename__ = "usage_stats"
    
    telegram_user_id = Column(BigInteger, primary_key=True)
    events_created = Column(Integer, default=0, nullable=False)
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    first_event_at = Column(DateTime(timezone=True), server_default=func.now())