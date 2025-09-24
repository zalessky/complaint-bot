from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.inline import AdminPanelCallback
from keyboards.inline import get_admin_panel_keyboard
from utils.db import get_admin_details, get_admin_stats, get_complaints_by_status
from utils.constants import ComplaintStatus
router = Router()
@router.message(F.text.lower() == 'панель администратора')
async def admin_panel_entry(message: Message):
    admin_info = await get_admin_details(message.from_user.id)
    if not admin_info:
        await message.answer('Панель администратора доступна только администраторам.')
        return
    stats = await get_admin_stats(admin_info['permissions'])
    await message.answer('Панель администратора', reply_markup=get_admin_panel_keyboard(stats))

@router.callback_query(AdminPanelCallback.filter(F.action == "show_new"))
async def show_new_complaints(callback: CallbackQuery, callback_data: AdminPanelCallback):
    admin_info = await get_admin_details(callback.from_user.id)
    complaints = await get_complaints_by_status([ComplaintStatus.NEW.value], admin_info.get('permissions', ['all']))
    if not complaints:
        await callback.answer("Нет записей.", show_alert=True)
        return
    txt = "<b>Новые жалобы</b>\n" + "\n".join([f"#{c['id']} | {c.get('address', '-')}" for c in complaints])
    await callback.message.answer(txt, parse_mode="HTML")
    await callback.answer()

@router.callback_query(AdminPanelCallback.filter(F.action == "show_in_work"))
async def show_inwork_complaints(callback: CallbackQuery, callback_data: AdminPanelCallback):
    admin_info = await get_admin_details(callback.from_user.id)
    complaints = await get_complaints_by_status(
        ["in_work", "clarification_needed"], admin_info.get('permissions', ['all'])
    )
    if not complaints:
        await callback.answer("Нет записей.", show_alert=True)
        return
    txt = "<b>В работе</b>\n" + "\n".join([f"#{c['id']} | {c.get('address', '-')}" for c in complaints])
    await callback.message.answer(txt, parse_mode="HTML")
    await callback.answer()
