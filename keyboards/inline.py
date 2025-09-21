# engels-transport-bot/keyboards/inline.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем из нового, нейтрального файла
from utils.constants import COMPLAINT_TYPES

def complaint_types_keyboard() -> InlineKeyboardMarkup:
    """Creates a keyboard with all complaint types."""
    buttons = []
    for type_id, type_name in COMPLAINT_TYPES.items():
        buttons.append([InlineKeyboardButton(text=type_name, callback_data=f"complaint_type_{type_id}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_complaint")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_datetime_keyboard(current_time: str) -> InlineKeyboardMarkup:
    """Creates a keyboard to confirm current time or enter manually."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сейчас", callback_data=f"datetime_confirm_{current_time}")],
        [InlineKeyboardButton(text="⌨️ Ввести вручную", callback_data="enter_manual_datetime")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_complaint")]
    ])
    return keyboard

def confirm_complaint_keyboard() -> InlineKeyboardMarkup:
    """Creates a keyboard to confirm or cancel the complaint submission."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить жалобу", callback_data="submit_complaint")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_complaint")]
    ])
    return keyboard
