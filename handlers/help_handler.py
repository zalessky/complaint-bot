from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("help"))
async def command_help(message: Message):
    text = ["<b>Справка по командам:</b>",
            "/start - Запустить бота",
            "/help - Показать эту справку",
            "/complaint - Подать обращение",
            "/panel - Панель администратора (только для админов)"]
    await message.answer("\n".join(text))
