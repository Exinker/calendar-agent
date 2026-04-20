# Calendar Bot - AGENTS.md

Multi-user Telegram bot with whitelist for adding events to shared Yandex/iCloud calendars via CalDAV.

## Quick Start

```bash
# First time setup
make setup              # Install deps, start PostgreSQL, run migrations

# Generate encryption key (required for .env)
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Configure .env then run
make run                # Starts Docker, migrations, then bot
```

## Essential Commands

| Command | Purpose |
|---------|---------|
| `make run` | Full startup (Docker → migrations → bot) |
| `make test` | Run all tests (smoke + integration if Docker available) |
| `make migrate-create` | Create new Alembic migration |
| `make init` | Seed admin user from ADMIN_USER_ID env var |

## Architecture

```
src/
api/telegram_handlers.py    # aiogram handlers with whitelist middleware
managers/                    # Business logic layer
  whitelist_manager.py      # Access control (is_user_whitelisted, add/remove)
  calendar_manager.py       # Gets encrypted credentials from DB
  event_logger.py           # Audit logging with user attribution
dao/database.py             # SQLAlchemy engine + session factory
models/
  config.py                 # Pydantic-settings from .env
  database_models.py        # SQLAlchemy: WhitelistUser, CalendarConfig, EventLog
  domain.py                 # Pydantic: ParsedEvent
services/
  calendar/yandex.py        # CalDAV client with dynamic credentials
  calendar/icloud.py        # Same interface, different URL
  llm_service.py            # OpenRouter with structured output
utils/encryption.py         # Fernet encryption for calendar passwords
```

## Key Workflows

### Adding a New User
1. Admin runs `/add_user <telegram_id>` in Telegram
2. User must then send `/start` to activate

### Database Changes
```bash
# After modifying models
cd /home/vagrant/code/calemdar-agent && uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Testing
- **Smoke tests** (`tests/test_basic.py`): Always run, no Docker needed
- **Integration tests** (`tests/integration/`): Require Docker; auto-skip if unavailable
- Use `testcontainers` for DB-dependent tests

## Environment Variables (Required)

```bash
TELEGRAM_BOT_TOKEN=       # From @BotFather
ADMIN_USER_ID=            # First admin Telegram ID
DATABASE_URL=             # postgresql+psycopg://bot_user:password@localhost:5432/calendar_bot
ENCRYPTION_KEY=           # Fernet key (generate with code above)
OPENROUTER_API_KEY=       # For LLM parsing
DEFAULT_CALENDAR=yandex   # yandex or icloud
TIMEZONE=Europe/Moscow
```

## Quirks

- **Credentials storage**: Calendar passwords stored encrypted in PostgreSQL; configure via `scripts/init_admin.py` or direct DB insert
- **No deletion via bot**: Events can only be deleted manually in calendar app
- **Single shared calendar**: All users add to the same calendar (configured in DB)
- **LLM parsing**: OpenRouter GPT-3.5-turbo; natasha as fallback commented out

## Database Schema

```sql
whitelist_users(telegram_id PK, role, is_active, added_by_telegram_id)
calendar_config(id, calendar_type, username, encrypted_password, is_active, is_default)
event_log(id, telegram_user_id, event_title, event_date, calendar_type, created_at)
```
