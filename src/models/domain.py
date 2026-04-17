from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ParsedEvent(BaseModel):
    """Parsed event from natural language."""
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    end_time: Optional[str] = Field(None, description="End time in HH:MM format")
    duration_minutes: Optional[int] = Field(60, description="Duration in minutes")
    is_recurring: bool = Field(False, description="Is recurring event")
    recurrence_rule: Optional[str] = Field(None, description="RRULE string")
    reminder_minutes_before: Optional[int] = Field(15, description="Reminder before event")
    confidence: float = Field(0.0, description="Confidence score 0-1")
    needs_clarification: bool = Field(False, description="Needs user clarification")
    clarification_question: Optional[str] = Field(None, description="Clarification question")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format")
        return v

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("start_time must be in HH:MM format")
        return v


class ParsedEventsList(BaseModel):
    """List of parsed events."""
    events: list[ParsedEvent] = Field(default_factory=list, description="List of parsed events")