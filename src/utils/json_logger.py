"""JSON logging utility to replace loguru."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from logging.handlers import RotatingFileHandler
from src.models.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as compact JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Добавляем exception info если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console."""
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # Формат: [HH:mm:ss] LEVEL module.function:line > message
        time_str = datetime.utcfromtimestamp(record.created).strftime("%H:%M:%S")
        location = f"{record.module}.{record.funcName}:{record.lineno}"

        if color:
            return f"{color}[{time_str}] {record.levelname:8} {location} > {record.getMessage()}{reset}"
        else:
            return (
                f"[{time_str}] {record.levelname:8} {location} > {record.getMessage()}"
            )


def setup_logging():
    """Setup logging with JSON format and rotation."""
    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Очищаем существующие хендлеры
    root_logger.handlers.clear()

    # Форматтеры
    json_formatter = JSONFormatter()
    console_formatter = ColoredFormatter()

    # Консольный вывод
    if settings.log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Файловый вывод с ротацией
    if settings.log_file:
        # Создаем директорию для логов если не существует
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Парсим размер из строки (например "10MB")
        max_bytes = parse_size(settings.log_rotation_size)

        file_handler = RotatingFileHandler(
            settings.log_file_path,
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)


def parse_size(size_str: str) -> int:
    """Parse size string like "10MB" to bytes."""
    size_str = size_str.upper().strip()
    multipliers = {"B": 1, "KB": 1024, "MB": 1024 * 1024, "GB": 1024 * 1024 * 1024}

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            try:
                number = float(size_str[: -len(suffix)])
                return int(number * multiplier)
            except ValueError:
                break

    # Дефолтное значение 10MB если не удалось распарсить
    return 10 * 1024 * 1024
