import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import start, help_handler, complaint_wizard, admin_panel, feedback_wizard, superadmin_panel
from keyboards.reply import set_default_commands
from utils.db import init_db, sync_superadmins, init_users_db
from utils.logger import setup_logging

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

async def main() -> None:
    bot = Bot(
        token=os.getenv("BOT_TOKEN", ""),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(help_handler.router)
    dp.include_router(complaint_wizard.router)
    dp.include_router(feedback_wizard.router)
    dp.include_router(admin_panel.router)
    dp.include_router(superadmin_panel.router)

    await set_default_commands(bot)
    
    await init_db()
    await init_users_db()
    logger.info("Databases initialized.")
    await sync_superadmins()
    logger.info("Superadmins synchronized.")

    logger.info("Starting bot…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
