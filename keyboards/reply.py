from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiogram import Bot

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Creates the main menu keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подать жалобу")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


async def set_default_commands(bot: Bot) -> None:
    """Sets the default commands for the bot menu."""
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Справка по работе бота"),
        BotCommand(command="menu", description="Показать главное меню"),
        BotCommand(command="complaint", description="Подать жалобу"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]
    await bot.set_my_commands(commands)
