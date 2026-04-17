# Calendar Agent - AGENTS.md

## Project Overview
Multi-user Telegram bot with whitelist that parses Russian natural language messages and adds events to shared Yandex/iCloud calendars via CalDAV. Only whitelisted users can add events.

## Tech Stack
- **Python 3.12**
- **uv** - Python package manager and virtual environment
- **aiogram** - Telegram bot framework
- **PostgreSQL** - Persistent storage for whitelist and event logs
- **SQLAlchemy + Alembic** - ORM and database migrations
- **psycopg** - PostgreSQL driver
- **cryptography** - Encryption for calendar credentials
- **pydantic-settings** - Configuration via `.env`
- **OpenRouter** - LLM provider for message parsing
- **caldav** - Calendar integration (Yandex + iCloud)
- **dateparser + natasha** - Fallback NLP if LLM unavailable

## Architecture
```
src/
├── api/                   # Telegram bot handlers
│   └── telegram_handlers.py
├── managers/              # Business logic
│   ├── whitelist_manager.py
│   └── calendar_manager.py
├── dao/                   # Data Access Objects (PostgreSQL)
│   ├── user_repository.py
│   ├── calendar_repository.py
│   └── event_repository.py
├── models/                # Pydantic and SQLAlchemy models
│   ├── config.py
│   ├── domain.py
│   └── database_models.py
├── services/              # External service integrations
│   ├── calendar/          # CalDAV clients
│   └── llm_service.py
└── utils/                 # Encryption, datetime utilities
    ├── encryption.py
    └── datetime_utils.py

main.py                    # Entry point
docker-compose.yml         # PostgreSQL container
Makefile                   # Build and deployment commands
migrations/                # Alembic database migrations
```

## Key Decisions
- **Whitelist-based access**: Only users in whitelist can use the bot
- **Single shared calendar**: One calendar per service, shared among whitelisted users
- **Admin-controlled**: Admin manages whitelist via Telegram commands
- **Encrypted credentials**: Calendar passwords encrypted in PostgreSQL
- **Event logging**: All created events logged with user attribution
- **PostgreSQL**: Persistent storage for whitelist and configuration
- **uv + Makefile**: Modern Python workflow with simple commands
- **LLM first, natasha fallback**: Try OpenRouter first, fall back to natasha if unavailable

## Environment Variables (.env)
```
TELEGRAM_BOT_TOKEN=
ADMIN_USER_ID=          # First admin, can add other users
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-3.5-turbo
DATABASE_URL=postgresql+psycopg://bot_user:password@localhost:5432/calendar_bot
ENCRYPTION_KEY=         # Key for encrypting calendar passwords
DEFAULT_CALENDAR=yandex
TIMEZONE=Europe/Moscow
```

## Admin Commands
- `/add_user <telegram_id>` - Add user to whitelist
- `/remove_user <telegram_id>` - Remove user from whitelist  
- `/list_users` - Show all whitelisted users

## User Commands
- `/start` - Check access and initialize
- `/stats` - Show my event statistics

## Database Schema
```sql
whitelist_users (telegram_id PK, username, role, added_at, is_active)
calendar_config (id, calendar_type, username, encrypted_password, is_active)
event_log (id, telegram_user_id, event_title, event_date, created_at)
```

## Setup Workflow
```bash
# 1. Setup environment
make setup              # Start PostgreSQL and run migrations

# 2. Add first user (admin)
make run
# Then: /add_user <admin_telegram_id>

# 3. Add calendar credentials
# Configure via admin commands or direct DB insert
```

## Calendar Integration
- Both Yandex and iCloud use **CalDAV** protocol
- Yandex URL: `https://caldav.yandex.ru`
- iCloud URL: `https://caldav.icloud.com`
- Use app-specific passwords, not account passwords
- Credentials encrypted with Fernet before storage

## Security
- Whitelist check on every message
- Calendar passwords encrypted in database
- Admin-only user management
- Event logging for audit trail
- No deletion permissions through bot (manual only)