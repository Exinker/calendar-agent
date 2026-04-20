"""Main entry point for the calendar bot."""

import asyncio
import logging

from src.utils.json_logger import setup_logging as init_logging
from src.api.telegram_handlers import main as run_bot


async def main():
    """Main entry point."""
    init_logging()
    logger = logging.getLogger(__name__)
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
