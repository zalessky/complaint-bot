import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage  # <--- ВОТ ЭТОТ НЕДОСТАЮЩИЙ ИМПОРТ

from handlers import start, help_handler, complaint_wizard, admin
from keyboards.reply import set_default_commands
from middlewares.access_control import AccessControlMiddleware
from middlewares.env_check import EnvCheckMiddleware
from utils.db import init_db
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function to start the bot."""
    # Check for mandatory environment variables before starting
    EnvCheckMiddleware.check_env_vars()

    # Initialize the bot with the new, correct syntax
    bot = Bot(
        token=os.getenv("BOT_TOKEN", ""),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register middlewares
    access_middleware = AccessControlMiddleware()
    dp.message.middleware(access_middleware)
    dp.callback_query.middleware(access_middleware)

    # Register routers
    dp.include_router(start.router)
    dp.include_router(help_handler.router)
    dp.include_router(complaint_wizard.router)
    dp.include_router(admin.router)

    # Set bot commands in Telegram menu
    await set_default_commands(bot)

    # Initialize the database
    await init_db()
    logger.info("Database initialized.")

    # Start the bot and skip any accumulated updates
    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
