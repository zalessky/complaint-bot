from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Подать жалобу")],
            [KeyboardButton(
                text="📋 Мои обращения",
                web_app=WebAppInfo(url="https://sterx.mooo.com:8443/webapp/residents")
            )],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🏙️ Добро пожаловать в Городской помощник!\n\n"
        "📝 Подать жалобу - создать обращение\n"
        "📋 Мои обращения - открыть историю в Mini App\n"
        "ℹ️ Помощь - информация",
        reply_markup=keyboard
    )

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    from backend.core.config import settings
    
    if message.from_user.id not in settings.admin_ids_list and message.from_user.id != settings.SUPER_ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎫 Панель управления",
                web_app=WebAppInfo(url="https://sterx.mooo.com:8443/webapp/services")
            )],
            [InlineKeyboardButton(
                text="📊 API Docs",
                url="https://sterx.mooo.com:8443/docs"
            )]
        ]
    )
    
    await message.answer(
        "🔧 Панель администратора\n\n"
        "Используйте Mini App для управления заявками:",
        reply_markup=keyboard
    )
