# Calendar Agent - AGENTS.md

## Project Overview
Telegram bot that parses Russian natural language messages and adds events to Yandex/iCloud calendars via CalDAV.

## Tech Stack
- **Python 3.9+**
- **aiogram** - Telegram bot framework
- **pydantic-settings** - Configuration via `.env`
- **OpenRouter** - LLM provider for message parsing
- **caldav** - Calendar integration (Yandex + iCloud)
- **dateparser + natasha** - Fallback NLP if LLM unavailable

## Architecture
```
config.py          - pydantic-settings configuration
llm_parser.py      - OpenRouter client with structured output
calendar_clients/  - Yandex + iCloud CalDAV clients
bot.py             - aiogram bot entrypoint
time_utils.py      - Timezone-aware datetime operations
```

## Key Decisions
- **Single-user** system with one active calendar at a time
- **App-specific passwords** required for iCloud (not main password)
- **Model selection** via `OPENROUTER_MODEL` env var
- **LLM first, fallback** to traditional NLP if LLM fails
- **Structured output** via Pydantic models for event parsing
- **Calendar switching** via `/calendar` and `/set_calendar` commands

## Environment Variables (.env)
```
TELEGRAM_BOT_TOKEN=
ADMIN_USER_ID=
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-3.5-turbo  # any OpenRouter model
YANDEX_ENABLED=true
YANDEX_USERNAME=
YANDEX_APP_PASSWORD=
ICLOUD_ENABLED=true
ICLOUD_USERNAME=
ICLOUD_APP_PASSWORD=
DEFAULT_CALENDAR=yandex
TIMEZONE=Europe/Moscow
```

## Commands
- `/start` - Initialize bot
- `/calendar` - Show current active calendar
- `/set_calendar <yandex|icloud>` - Switch active calendar
- `/calendars` - List available calendars
- Natural language messages - Parse and create events

## LLM Prompt Pattern
- Inject current datetime into prompt for relative date resolution
- Use `response_format: {"type": "json_object"}` for structured output
- Parse response into Pydantic `ParsedEvent` model
- Validate dates are reasonable (not far past/future)

## Calendar Integration
- Both Yandex and iCloud use **CalDAV** protocol
- Yandex URL: `https://caldav.yandex.ru`
- iCloud URL: `https://caldav.icloud.com`
- Use app-specific passwords, not account passwords
