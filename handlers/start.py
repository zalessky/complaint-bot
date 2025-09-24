from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from keyboards.reply import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def command_start(message: Message):
    await message.answer("Привет! Я бот для сбора обращений по городским проблемам.", reply_markup=main_menu_keyboard())

@router.message(Command("menu"))
async def command_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())

@router.message(F.text.lower() == "направить благодарность")
async def handle_gratitude(msg: Message):
    await msg.answer("Функционал 'благодарности' будет добавлен позже!")
