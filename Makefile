.PHONY: help install dev-install run test lint format migrate-up migrate-down docker-up docker-down clean setup

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies with uv"
	@echo "  make dev-install  - Install development dependencies with uv"
	@echo "  make run          - Start infrastructure, run migrations and start bot"
	@echo "  make setup        - One-time setup: install deps and start infrastructure"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter (ruff)"
	@echo "  make format       - Format code (black)"
	@echo "  make migrate-up   - Run database migrations (upgrade)"
	@echo "  make migrate-down - Revert database migrations (downgrade)"
	@echo "  make docker-up    - Start PostgreSQL with docker compose"
	@echo "  make docker-down  - Stop PostgreSQL containers"
	@echo "  make clean        - Clean cache files and virtual environment"

# Installation
install:
	uv sync

dev-install:
	uv sync --all-extras

# Docker infrastructure
docker-up:
	docker compose up -d
	@echo "Waiting for PostgreSQL to start..."
	@sleep 3

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f postgres

# Database migrations
migrate-up:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

migrate-create:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

# Setup (one-time setup)
setup: install docker-up migrate-up
	@echo "✓ Setup complete! Run 'make run' to start the bot."

# Initialize admin and calendar from environment variables
init:
	uv run python scripts/init_admin.py

# Run bot (start infra + migrations + bot)
run: docker-up
	@echo "Running migrations..."
	@uv run alembic upgrade head
	@echo "Starting bot..."
	@uv run python main.py

# Testing
test:
	uv run pytest tests/ -v

test-integration:
	uv run pytest tests/integration/ -v

# Code quality
lint:
	uv run ruff check src/
	uv run ruff check tests/

lint-fix:
	uv run ruff check src/ --fix
	uv run ruff check tests/ --fix

format:
	uv run black src/ tests/

format-check:
	uv run black --check src/ tests/

# Clean
clean:
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov

db-reset: docker-down
	docker compose down -v
	rm -rf postgres_data
	@echo "Database volume removed. Run 'make run' to create fresh database."