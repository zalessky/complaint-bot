from aiogram import Bot
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, BotCommand
from typing import Optional

def main_menu_keyboard(role: Optional[str] = None) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📝 Подать жалобу"), KeyboardButton(text="📢 Обратная связь")],
        [KeyboardButton(text="🆘 Справка/О сервисе")]
    ]
    if role in ('admin', 'superadmin'):
        buttons.append([KeyboardButton(text="🛠️ Панель администратора")])
    if role == 'superadmin':
        buttons.append([KeyboardButton(text="👑 Панель Суперадминистратора")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад в Главное меню")]],
        resize_keyboard=True
    )

def get_cancel_keyboard(request_contact: bool = False, finish_photo: bool = False) -> ReplyKeyboardMarkup:
    keyboard = []
    if request_contact:
        keyboard.append([KeyboardButton(text="Отправить мой номер телефона", request_contact=True)])
    if finish_photo:
        keyboard.append([KeyboardButton(text="Завершить добавление фото")])
        
    keyboard.append([KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, selective=True)

def get_location_keyboard(geo_required: bool = False) -> ReplyKeyboardMarkup:
    keyboard = []
    if geo_required:
        keyboard.append([KeyboardButton(text='📍 Отправить геолокацию', request_location=True)])
    keyboard.append([KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True, selective=True)

async def set_default_commands(bot: Bot) -> None:
    # Sending an empty list removes the menu button
    await bot.set_my_commands([])
