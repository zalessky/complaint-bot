from aiogram import Bot
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def main_menu_keyboard(is_admin=False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Подать жалобу"), KeyboardButton(text="Направить благодарность")],
        [KeyboardButton(text="Справка/О сервисе")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="Панель администратора")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

async def set_default_commands(bot: Bot) -> None:
    await bot.set_my_commands([])
