import asyncio, logging, os
from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import start, help_handler, complaint_wizard, admin_panel
from keyboards.reply import set_default_commands
from middlewares.access_control import IsAdminFilter  # ← был AccessControlMiddleware
from utils.db import init_db
from utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

async def main() -> None:
    bot = Bot(
        token=os.getenv("BOT_TOKEN", ""),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Глобальные middleware не подключаем.
    # Права доступа проверяются точечно через IsAdminFilter в нужных хэндлерах.

    dp.include_router(start.router)
    dp.include_router(help_handler.router)
    dp.include_router(complaint_wizard.router)
    dp.include_router(admin_panel.router)

    await set_default_commands(bot)
    await init_db()
    logger.info("Database initialized.")

    logger.info("Starting bot…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
