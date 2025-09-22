from aiogram import Bot
from aiogram.types import BotCommand, KeyboardButton, ReplyKeyboardMarkup

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Подать жалобу")]], resize_keyboard=True)

def request_location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Отправить мое местоположение", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)

async def set_default_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="complaint", description="Подать жалобу"),
        BotCommand(command="panel", description="Панель администратора"),
    ]
    await bot.set_my_commands(commands)
