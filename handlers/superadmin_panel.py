import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from keyboards.reply import main_menu_keyboard
from middlewares.access_control import IsAdminFilter
from utils.db import get_admin_details, get_all_users_with_stats

router = Router()
logger = logging.getLogger(__name__)

async def superadmin_panel_entry(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    admin_info = await get_admin_details(user_id)
    role = admin_info.get('role') if admin_info else None

    await message.answer("Загружаю панель суперадминистратора...", reply_markup=ReplyKeyboardRemove())
    
    all_users = await get_all_users_with_stats()
    total_users = len(all_users)

    max_users_to_show = 50
    limited_users = all_users[:max_users_to_show]
    
    header = (
        f"👑 <b>Панель Суперадминистратора</b>\n"
        f"📊 <b>Всего пользователей в боте:</b> {total_users}\n\n"
        f"📋 <b>Последние {len(limited_users)} активных пользователей:</b>\n"
        f"<code>ID | Nickname | Имя | Жалоб | Первый/Последний визит</code>\n"
        f"--------------------------------------------------\n"
    )

    user_lines = []
    for user in limited_users:
        user_id_str = str(user['user_id'])
        username = f"@{user['username']}" if user.get('username') else "-"
        first_name = user.get('first_name', 'N/A')
        complaint_count = user['complaint_count']
        first_seen = user['first_seen'][:16].replace('T', ' ')
        last_seen = user['last_seen'][:16].replace('T', ' ')
        user_lines.append(f"<code>{user_id_str:<10} | {username[:10]:<10} | {first_name[:10]:<10} | {complaint_count:<5} | {first_seen} / {last_seen}</code>")

    report = header + "\n".join(user_lines)
    if total_users > max_users_to_show:
        report += f"\n... и еще {total_users - max_users_to_show} пользователей."
    
    await message.answer(report, reply_markup=main_menu_keyboard(role))
