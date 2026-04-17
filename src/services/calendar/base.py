"""Base calendar client interface."""
from abc import ABC, abstractmethod
from typing import List

from src.models.domain import ParsedEvent


class BaseCalendarClient(ABC):
    """Abstract base class for calendar clients."""
    
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self._client = None
    
    @abstractmethod
    def _get_client(self):
        """Get or create calendar client instance."""
        pass
    
    @abstractmethod
    def _get_principal(self):
        """Get calendar principal."""
        pass
    
    @abstractmethod
    def create_event(self, event: ParsedEvent) -> str:
        """Create event in calendar."""
        pass
    
    @abstractmethod
    def get_calendars(self) -> List:
        """Get list of available calendars."""
        pass