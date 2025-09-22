# handlers/admin_panel.py
import asyncio, logging
from typing import Any, Dict

from aiogram import F, Router, html, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards.inline import (
    AdminPanelCallback,
    ComplaintActionCallback,
    ComplaintStatusCallback,
    get_admin_panel_keyboard,
    get_complaint_actions_keyboard,
    get_status_selection_keyboard,
)
from middlewares.access_control import IsAdminFilter
from utils.constants import ComplaintStatus
from utils.db import (
    add_history_record,
    assign_complaint_to_admin,
    get_admin_details,
    get_admin_stats,
    get_complaint_by_id,
    get_complaints_by_status,
    get_complaint_history,
    update_complaint_status,
)

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdminFilter())          # доступ к сообщениям
router.callback_query.filter(IsAdminFilter())   # доступ к кнопкам

# ---------- Форматирование карточки обращения ----------
async def format_complaint(c: Dict[str, Any]) -> str:
    lines = [
        f'<b>Обращение #{c["id"]}</b> | <b>Статус: {c["status"]}</b>',
        f'<i>{c["created_at"]}</i>',
        f'<b>Категория:</b> {html.quote(c["category_key"])} -> {html.quote(c["subcategory_name"])}',
    ]
    if c.get("route_number"):
        lines.append(f'<b>Номер ТС:</b> {html.quote(c["route_number"])}')
    if c.get("violation_datetime"):
        lines.append(f'<b>Время:</b> {c["violation_datetime"]}')
    if c.get("address"):
        lines.append(f'<b>Адрес:</b> {html.quote(c["address"])}')
    if c.get("description"):
        lines.append(f'<b>Описание:</b> {html.quote(c["description"])}')
    if c.get("assigned_admin_id"):
        lines.append(f'<b>В работе у:</b> ID {c["assigned_admin_id"]}')
    return "\n".join(lines)

# ---------- Команда /panel ----------
@router.message(Command("panel"))
async def cmd_panel(message: Message):
    """Стартовая панель администратора."""
    admin_info = await get_admin_details(message.from_user.id)
    if not admin_info:
        return await message.answer("⛔️ У вас нет прав администратора.")
    stats = await get_admin_stats(admin_info["permissions"])
    await message.answer("Панель администратора", reply_markup=get_admin_panel_keyboard(stats))

# ---------- Список обращений ----------
@router.callback_query(AdminPanelCallback.filter(F.action.in_({"show_new", "show_in_work"})))
async def show_complaints(callback: CallbackQuery, callback_data: AdminPanelCallback):
    admin_info = await get_admin_details(callback.from_user.id)
    status_map = {
        "show_new":    [ComplaintStatus.NEW.value],
        "show_in_work": [ComplaintStatus.IN_WORK.value, ComplaintStatus.CLARIFICATION_NEEDED.value],
    }
    statuses_to_fetch = status_map[callback_data.action]
    complaints = await get_complaints_by_status(statuses_to_fetch, admin_info["permissions"])
    if not complaints:
        return await callback.answer("Нет обращений в этом статусе.", show_alert=True)

    await callback.message.answer(
        f'<b>Список обращений (статус: {", ".join(statuses_to_fetch)})</b>:'
    )
    for c in complaints:
        await callback.message.answer(
            await format_complaint(c),
            reply_markup=get_complaint_actions_keyboard(c["id"]),
        )
    await callback.answer()

# ---------- Принять в работу ----------
@router.callback_query(ComplaintActionCallback.filter(F.action == "accept"))
async def accept_complaint(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    admin_id = callback.from_user.id
    complaint_id = callback_data.complaint_id
    await assign_complaint_to_admin(complaint_id, admin_id)
    await add_history_record(
        complaint_id, admin_id, "status_change",
        "Статус изменен с 'new' на 'in_work'.",
    )
    await callback.message.edit_text(
        f"{callback.message.html_text}\n--- \n<b>✅ Принято в работу вами.</b>"
    )
    await callback.answer("Жалоба принята в работу!")

# ---------- Управление статусом ----------
@router.callback_query(ComplaintActionCallback.filter(F.action == "manage"))
async def manage_complaint(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    await callback.message.edit_reply_markup(
        reply_markup=get_status_selection_keyboard(callback_data.complaint_id)
    )
    await callback.answer()

@router.callback_query(ComplaintActionCallback.filter(F.action == "back_to_actions"))
async def back_to_actions(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    await callback.message.edit_reply_markup(
        reply_markup=get_complaint_actions_keyboard(callback_data.complaint_id)
    )
    await callback.answer()

@router.callback_query(ComplaintStatusCallback.filter())
async def process_status_change(
    callback: CallbackQuery,
    callback_data: ComplaintStatusCallback,
    bot: Bot,
):
    complaint = await get_complaint_by_id(callback_data.complaint_id)
    if not complaint:
        return await callback.answer("Обращение не найдено", show_alert=True)

    admin_id = callback.from_user.id
    new_status = ComplaintStatus(callback_data.status)
    old_status = complaint["status"]

    await update_complaint_status(callback_data.complaint_id, new_status)
    await add_history_record(
        callback_data.complaint_id,
        admin_id,
        "status_change",
        f"Статус изменен с '{old_status}' на '{new_status.value}'.",
    )
    try:
        await bot.send_message(
            complaint["user_id"],
            f"Статус вашего обращения #{callback_data.complaint_id} изменен на: <b>{new_status.value}</b>.",
        )
    except Exception as e:
        logger.warning(f'Cannot notify user {complaint["user_id"]}: {e}')

    await callback.message.edit_text(
        f"{callback.message.html_text}\n--- \n<b>🔄 Статус изменен на: {new_status.value}</b>"
    )
    await callback.answer(
        f"Статус обращения #{callback_data.complaint_id} изменен.", show_alert=True
    )

# ---------- История ----------
@router.callback_query(ComplaintActionCallback.filter(F.action == "history"))
async def show_history(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    history = await get_complaint_history(callback_data.complaint_id)
    if not history:
        return await callback.answer("История пуста.", show_alert=True)
    lines = ["<b>История обращения:</b>"] + [
        f'- <i>{r["timestamp"]}</i>: {html.quote(r["details"])}'
        for r in history
    ]
    await callback.message.answer("\n".join(lines))
    await callback.answer()
