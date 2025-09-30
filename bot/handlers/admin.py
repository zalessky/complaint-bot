from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from backend.core.config import settings

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in settings.admin_ids_list and message.from_user.id != settings.SUPER_ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎫 Панель управления (Тикет-трекер)",
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
        "🔧 Панель администратора\n\n"
        "🎫 Панель управления - тикет-трекер с канбан-доской\n"
        "📊 API - техническая документация\n"
        "📈 Статистика - общие показатели",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from backend.db.database import AsyncSessionLocal
        from backend.db import crud
        from sqlalchemy import select, func
        from backend.db.models import Complaint
        
        async with AsyncSessionLocal() as db:
            # Подсчет жалоб по статусам
            result = await db.execute(
                select(Complaint.status, func.count(Complaint.id))
                .group_by(Complaint.status)
            )
            stats = dict(result.all())
            
            total = await db.execute(select(func.count(Complaint.id)))
            total_count = total.scalar()
            
            text = (
                "📈 Статистика обращений:\n\n"
                f"📊 Всего: {total_count}\n"
                f"🆕 Новых: {stats.get('new', 0)}\n"
                f"⚙️ В работе: {stats.get('in_progress', 0)}\n"
                f"✅ Решено: {stats.get('resolved', 0)}\n"
            )
            
            await callback.message.answer(text)
    except Exception as e:
        await callback.message.answer(f"Ошибка получения статистики: {e}")
    
    await callback.answer()
