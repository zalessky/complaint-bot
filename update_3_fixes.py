#!/usr/bin/env python3
"""
Обновление 3: Исправления и админская кнопка
"""
print("📦 Обновление 3: Исправления")
print("="*60)

# 1. Обновляем start handler с кнопкой админки
start_handler = '''from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from backend.core.config import settings

router = Router()

def get_main_keyboard(user_id: int):
    """Возвращает клавиатуру в зависимости от прав пользователя"""
    is_admin = user_id in settings.admin_ids_list or user_id == settings.SUPER_ADMIN_ID
    
    if is_admin:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Подать жалобу")],
                [KeyboardButton(
                    text="📋 Мои обращения",
                    web_app=WebAppInfo(url="https://sterx.mooo.com:8443/webapp/residents")
                )],
                [KeyboardButton(text="✅ Благодарность"), KeyboardButton(text="💬 Обратная связь")],
                [KeyboardButton(text="🔧 Панель администратора")],
                [KeyboardButton(text="ℹ️ Помощь")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Подать жалобу")],
                [KeyboardButton(
                    text="📋 Мои обращения",
                    web_app=WebAppInfo(url="https://sterx.mooo.com:8443/webapp/residents")
                )],
                [KeyboardButton(text="✅ Благодарность"), KeyboardButton(text="💬 Обратная связь")],
                [KeyboardButton(text="ℹ️ Помощь")]
            ],
            resize_keyboard=True
        )
    
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = get_main_keyboard(message.from_user.id)
    await message.answer(
        "🏙️ Добро пожаловать в Городской помощник!\\n\\n"
        "📝 Подать жалобу - создать обращение\\n"
        "📋 Мои обращения - открыть историю\\n"
        "✅ Благодарность - поблагодарить сотрудников\\n"
        "💬 Обратная связь - предложение или ошибка\\n"
        "ℹ️ Помощь - информация",
        reply_markup=keyboard
    )

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    await show_admin_panel(message)

@router.message(lambda message: message.text == "🔧 Панель администратора")
async def btn_admin_panel(message: types.Message):
    await show_admin_panel(message)

async def show_admin_panel(message: types.Message):
    """Показывает панель администратора"""
    if message.from_user.id not in settings.admin_ids_list and message.from_user.id != settings.SUPER_ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎫 Тикет-трекер (Канбан)",
                web_app=WebAppInfo(url="https://sterx.mooo.com:8443/webapp/services")
            )],
            [InlineKeyboardButton(
                text="📊 API документация",
                url="https://sterx.mooo.com:8443/docs"
            )],
            [InlineKeyboardButton(
                text="📈 Статистика",
                callback_data="admin_stats"
            )]
        ]
    )
    
    await message.answer(
        "🔧 Панель администратора\\n\\n"
        "🎫 Тикет-трекер - управление заявками\\n"
        "📊 API - техническая документация\\n"
        "📈 Статистика - общие показатели",
        reply_markup=keyboard
    )
'''

with open("bot/handlers/start.py", "w", encoding="utf-8") as f:
    f.write(start_handler)

print("✅ Обновлен bot/handlers/start.py")
print("  • Добавлена кнопка 'Панель администратора' для админов")
print("  • Динамическое меню в зависимости от прав")

# 2. Проверяем текущую структуру БД
print("\n📊 Проверка структуры БД...")
import sqlite3
try:
    conn = sqlite3.connect('data/complaints.sqlite3')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(complaints)")
    columns = cursor.fetchall()
    print("  Колонки в таблице complaints:")
    for col in columns:
        print(f"    • {col[1]} ({col[2]})")
    conn.close()
except Exception as e:
    print(f"  ⚠️  Не удалось проверить БД: {e}")

print("\n" + "="*60)
print("✅ Обновление 3 завершено!")
print("\n📝 Следующие шаги:")
print("  1. Перезапустите бота: bash stop_app.sh && bash start_app.sh")
print("  2. Проверьте кнопку 'Панель администратора'")
print("  3. Проверьте загрузку 'Мои обращения'")
