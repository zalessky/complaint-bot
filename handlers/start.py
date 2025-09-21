import logging

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards.reply import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Handles the /start command."""
    logger.info("User %s started bot.", message.from_user.id)
    await message.answer(
        "Привет! Я бот для сбора жалоб на городской транспорт Энгельса.\n"
        "Используйте /menu для доступа к основным функциям.\n"
        "Для подробной информации наберите /help.",
        reply_markup=main_menu_keyboard(),
    )

@router.message(Command("menu"))
async def command_menu_handler(message: Message) -> None:
    """Handles the /menu command."""
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
