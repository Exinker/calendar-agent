import json
import logging
import httpx

from src.models.config import settings
from src.models.domain import ParsedEvent, ParsedEventsList
from src.utils.datetime_utils import get_current_datetime_str, validate_date_range


SYSTEM_PROMPT = """Ты помощник для извлечения информации о событиях из сообщений на русском языке.

ШАГИ:
1. Сначала вызови инструмент get_current_datetime чтобы узнать текущую дату
2. Затем извлеки ВСЕ события из сообщения и верни JSON СТРОГО по схеме ниже

СХЕМА JSON (обязательные поля):
{
    "events": [
        {
            "title": "строка - название события",
            "description": "строка или null - описание",
            "start_date": "строка - YYYY-MM-DD",
            "start_time": "строка - HH:MM в 24h формате",
            "end_date": "строка или null",
            "end_time": "строка или null",
            "duration_minutes": число или null,
            "is_recurring": true или false,
            "recurrence_rule": "строка или null",
            "reminder_minutes_before": число или null,
            "confidence": число от 0.0 до 1.0,
            "needs_clarification": true или false,
            "clarification_question": "строка или null"
        }
    ]
}

ВАЖНО:
- Поля title, start_date, start_time — ОБЯЗАТЕЛЬНЫЕ для каждого события
- Не используй поля типа "event", "day", "time" — используй ТОЛЬКО поля из схемы
- start_date должен быть в формате YYYY-MM-DD
- start_time должен быть в формате HH:MM
- Если в сообщении несколько событий — верни массив events со всеми ними
- Если день недели указан без даты (например "Вторник") — вычисли ближайшую будущую дату этого дня недели
- Если время не указано — ставь 10:00 по умолчанию"""


logger = logging.getLogger(__name__)


async def parse_events_with_llm(message: str) -> ParsedEventsList:
    """Parse events from natural language using LLM."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "https://calendar-bot.local",
                "X-Title": "Calendar Bot",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_current_datetime",
                            "description": "Get current date and time for resolving relative dates",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                "tool_choice": {
                    "type": "function",
                    "function": {"name": "get_current_datetime"},
                },
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    current_dt = get_current_datetime_str()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
        data["choices"][0]["message"],
        {
            "role": "tool",
            "tool_call_id": data["choices"][0]["message"]["tool_calls"][0]["id"],
            "content": json.dumps({"current_datetime": current_dt}),
        },
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "https://calendar-bot.local",
                "X-Title": "Calendar Bot",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    logger.debug(f"LLM response: {content}")

    parsed_list = ParsedEventsList.model_validate(json.loads(content))

    for event in parsed_list.events:
        if not validate_date_range(event.start_date):
            raise ValueError(f"Дата {event.start_date} выходит за допустимый диапазон")

    return parsed_list
