import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.reply import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """Handles the /help command."""
    logger.info("User %s requested help.", message.from_user.id)
    help_text = (
        "<b>Я бот \"Городской Транспорт. Энгельс\".</b>\n\n"\
        "<b>Доступные команды:</b>\n"\
        "/start - Начать взаимодействие с ботом\n"\
        "/help - Показать эту справку\n"\
        "/menu - Открыть главное меню\n"\
        "/complaint - Начать подачу жалобы\n"\
        "/cancel - Отменить текущий процесс\n\n"\
        "<b>Административные команды:</b>\n"\
        "/stats - Статистика по жалобам\n"\
        "/last N - Последние N жалоб\n"\
        "/export - Экспорт жалоб в CSV\n"\
        "/setstatus &lt;id&gt; &lt;status&gt; - Установить статус жалобы\n\n"\
        "Для подачи жалобы используйте команду /complaint или кнопку 'Подать жалобу' в меню.\n"
    )
    await message.answer(help_text, reply_markup=main_menu_keyboard())
