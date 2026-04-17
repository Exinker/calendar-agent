"""Main entry point for the calendar bot."""
import asyncio
import logging
from loguru import logger

from src.api.telegram_handlers import main as run_bot


def setup_logging():
    """Setup logging configuration."""
    logger.add(
        "logs/bot.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


async def main():
    """Main entry point."""
    setup_logging()
    logger.info("Starting Calendar Bot v2.0.0")
    
    try:
        await run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())