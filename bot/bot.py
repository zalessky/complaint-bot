import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from backend.core.config import settings

# Импортируем handlers через относительные импорты
from .handlers import start, complaint, admin

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(complaint.router)
    dp.include_router(admin.router)

    logger.info("🤖 Telegram бот запущен (polling)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
