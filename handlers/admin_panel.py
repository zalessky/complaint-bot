import logging
import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from keyboards.inline import (
    AdminPanelCallback, get_admin_panel_keyboard, get_complaint_list_keyboard,
    get_complaint_actions_keyboard, ComplaintActionCallback, ComplaintStatusCallback,
    get_status_selection_keyboard
)
from keyboards.reply import admin_menu_keyboard # Import the new admin keyboard
from middlewares.access_control import IsAdminFilter
from utils.db import get_admin_details, get_admin_stats, get_complaints_by_status, get_complaint_by_id, update_complaint_status, get_media_by_complaint_id
from utils.constants import ComplaintStatus, STATUS_LABEL_RU, CATEGORIES
from utils.export import export_complaints_to_csv

router = Router()
logger = logging.getLogger(__name__)

async def show_admin_panel_from_main_menu(message: Message, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(message.from_user.id)
    if not admin_info:
        await message.answer('Эта команда доступна только администраторам.')
        return
    await message.answer("Загружаю панель администратора...", reply_markup=admin_menu_keyboard())
    stats = await get_admin_stats()
    await message.answer('Панель администратора', reply_markup=get_admin_panel_keyboard(stats))

@router.message(Command('panel'), IsAdminFilter())
async def admin_panel_entry_command(message: Message, state: FSMContext):
    await show_admin_panel_from_main_menu(message, state)

@router.callback_query(AdminPanelCallback.filter(F.action.startswith("show_")))
async def show_complaints_by_status_group(callback: CallbackQuery, callback_data: AdminPanelCallback, state: FSMContext):
    action = callback_data.action.split('_', 1)[1]
    await state.update_data(current_list_action=callback_data.action)
    status_map = {
        "new": ("Новые", [ComplaintStatus.NEW.value]),
        "in_work": ("В работе", [ComplaintStatus.IN_WORK.value, ComplaintStatus.CLARIFICATION_NEEDED.value]),
        "completed": ("Завершенные", [ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value, ComplaintStatus.CLOSED.value]),
        "all": ("Все", [s.value for s in ComplaintStatus])
    }
    
    title, statuses_to_fetch = status_map.get(action, (None, []))
    if not statuses_to_fetch:
        await callback.answer("Неизвестное действие.", show_alert=True)
        return

    complaints = await get_complaints_by_status(statuses_to_fetch)
    if not complaints:
        await callback.answer("В этой категории нет обращений.", show_alert=True)
        return

    await callback.message.edit_text(
        f"<b>{title} обращения:</b>",
        reply_markup=get_complaint_list_keyboard(complaints, current_list_action=callback_data.action)
    )
    await callback.answer()

@router.callback_query(ComplaintActionCallback.filter(F.action == "view"))
async def view_complaint(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    complaint_id = callback_data.complaint_id
    complaint = await get_complaint_by_id(complaint_id)
    if not complaint:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    media = await get_media_by_complaint_id(complaint_id)
    
    card_title = "Жалоба" if complaint['category_key'] not in ['gratitude', 'feedback'] else "Обратная связь"
    location_title = "Место/Маршрут" if complaint['category_key'] not in ['gratitude', 'feedback'] else "Кому/Тема"
    location_data = complaint.get('address') or complaint.get('route_number')

    card = (
        f"<b>{card_title} #{complaint['id']}</b>\n"
        f"<b>Статус:</b> {STATUS_LABEL_RU.get(complaint['status'], complaint['status'])}\n"
        f"<b>Категория:</b> {CATEGORIES.get(complaint['category_key'], {}).get('name', complaint['category_key'])}\n"
        f"<b>Подкатегория:</b> {complaint.get('subcategory_name', '-')}\n"
        f"<b>{location_title}:</b> {location_data or '-'}\n"
        f"<b>Описание:</b> {complaint.get('description', '-')}\n"
        f"<b>ФИО:</b> {complaint.get('fio', '-')}\n"
        f"<b>Телефон:</b> {complaint.get('phone', '-')}\n"
        f"<b>Отправитель:</b> @{complaint.get('username', complaint['user_id'])}\n"
        f"<b>Дата:</b> {complaint['created_at']}"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    if media:
        media_group = [InputMediaPhoto(media=m['file_id']) for m in media]
        await callback.message.answer_media_group(media=media_group)
    
    await callback.message.answer(card, reply_markup=get_complaint_actions_keyboard(complaint_id, back_action="back_to_list"))
    await callback.answer()

@router.callback_query(ComplaintActionCallback.filter(F.action == "change_status"))
async def change_status_menu(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "Выберите новый статус:",
        reply_markup=get_status_selection_keyboard(callback_data.complaint_id)
    )
    await callback.answer()

@router.callback_query(ComplaintStatusCallback.filter(F.action == "set_status"))
async def set_complaint_status(callback: CallbackQuery, callback_data: ComplaintStatusCallback):
    complaint_id = callback_data.complaint_id
    new_status = callback_data.status
    
    await update_complaint_status(complaint_id, new_status)
    await callback.answer(f"Статус изменен на '{STATUS_LABEL_RU.get(new_status)}'", show_alert=True)

    await callback.message.delete()
    stats = await get_admin_stats()
    await callback.message.answer('Панель администратора', reply_markup=get_admin_panel_keyboard(stats))

@router.callback_query(AdminPanelCallback.filter(F.action == "back_to_panel"))
async def back_to_admin_panel(callback: CallbackQuery):
    stats = await get_admin_stats()
    await callback.message.edit_text('Панель администратора', reply_markup=get_admin_panel_keyboard(stats))
    await callback.answer()

@router.callback_query(ComplaintActionCallback.filter(F.action == "back_to_list"))
async def back_to_list_from_view(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.delete()
    current_list_action = (await state.get_data()).get('current_list_action', 'show_all')
    await callback.answer()
    await show_complaints_by_status_group(callback, AdminPanelCallback(action=current_list_action), state)

@router.message(Command('export'), IsAdminFilter())
async def export_data(message: Message):
    try:
        file_path = await export_complaints_to_csv()
        await message.answer_document(FSInputFile(file_path), caption="Выгрузка всех обращений в формате CSV.")
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        await message.answer("Произошла ошибка при формировании отчета.")
