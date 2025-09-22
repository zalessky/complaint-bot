import asyncio, logging
from typing import Any, Dict

from aiogram import F, Router, html, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from keyboards.inline import (
    AdminPanelCallback,
    ComplaintActionCallback,
    ComplaintStatusCallback,
    get_admin_panel_keyboard,
    get_complaint_actions_keyboard,
    get_status_selection_keyboard,
)
from middlewares.access_control import IsAdminFilter
from utils.constants import ComplaintStatus, STATUS_LABEL_RU
from utils.db import (
    add_history_record,
    assign_complaint_to_admin,
    get_admin_details,
    get_admin_stats,
    get_complaint_by_id,
    get_complaints_by_status,
    get_complaint_history,
    get_media_file_ids,
    update_complaint_status,
)

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


async def format_complaint(c: Dict[str, Any]) -> str:
    lines = [
        f'<b>Обращение #{c["id"]}</b> | <b>Статус: {STATUS_LABEL_RU.get(c["status"], c["status"])}</b>',
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


@router.message(Command("panel"))
async def cmd_panel(message: Message):
    admin_info = await get_admin_details(message.from_user.id)
    if not admin_info:
        return await message.answer("⛔️ У вас нет прав администратора.")
    stats = await get_admin_stats(admin_info["permissions"])
    await message.answer("Панель администратора", reply_markup=get_admin_panel_keyboard(stats))


@router.callback_query(AdminPanelCallback.filter(F.action.in_({"show_new", "show_in_work"})))
async def show_complaints(callback: CallbackQuery, callback_data: AdminPanelCallback):
    admin_info = await get_admin_details(callback.from_user.id)
    status_map = {
        "show_new": [ComplaintStatus.NEW.value],
        "show_in_work": [ComplaintStatus.IN_WORK.value, ComplaintStatus.CLARIFICATION_NEEDED.value],
    }
    statuses_to_fetch = status_map[callback_data.action]
    complaints = await get_complaints_by_status(statuses_to_fetch, admin_info["permissions"])
    if not complaints:
        return await callback.answer("Нет обращений в этом статусе.", show_alert=True)

    human = ", ".join(STATUS_LABEL_RU[s] for s in statuses_to_fetch)
    await callback.message.answer(f"<b>Список обращений (статус: {human})</b>:")

    for c in complaints:
        # Текстовая карточка
        await callback.message.answer(
            await format_complaint(c),
            reply_markup=get_complaint_actions_keyboard(c["id"]),
        )
        # Медиа-группа до 3 фото
        media_ids = await get_media_file_ids(c["id"])
        if media_ids:
            media_group = [InputMediaPhoto(media=m) for m in media_ids[:3]]
            try:
                await callback.message.answer_media_group(media=media_group)
            except Exception as e:
                logger.warning(f"Media group send failed for complaint {c['id']}: {e}")
    await callback.answer()


@router.callback_query(ComplaintActionCallback.filter(F.action == "accept"))
async def accept_complaint(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    admin_id = callback.from_user.id
    complaint_id = callback_data.complaint_id
    await assign_complaint_to_admin(complaint_id, admin_id)
    await add_history_record(
        complaint_id, admin_id, "status_change", "Статус изменен с 'Новое' на 'В работе'."
    )
    await callback.message.edit_text(
        f"{callback.message.html_text}\n--- \n<b>✅ Принято в работу вами.</b>"
    )
    await callback.answer("Жалоба принята в работу!")


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
        f"Статус изменен с '{STATUS_LABEL_RU.get(old_status, old_status)}' на '{STATUS_LABEL_RU[new_status.value]}'.",
    )
    try:
        await bot.send_message(
            complaint["user_id"],
            f"Статус вашего обращения #{callback_data.complaint_id} изменен на: <b>{STATUS_LABEL_RU[new_status.value]}</b>.",
        )
    except Exception as e:
        logger.warning(f"Could not notify user {complaint['user_id']}: {e}")

    await callback.message.edit_text(
        f"{callback.message.html_text}\n--- \n<b>🔄 Статус изменен на: {STATUS_LABEL_RU[new_status.value]}</b>"
    )
    await callback.answer(
        f"Статус обращения #{callback_data.complaint_id} изменен.", show_alert=True
    )


@router.callback_query(ComplaintActionCallback.filter(F.action == "history"))
async def show_history(callback: CallbackQuery, callback_data: ComplaintActionCallback):
    history = await get_complaint_history(callback_data.complaint_id)
    if not history:
        return await callback.answer("История пуста.", show_alert=True)
    lines = ["<b>История обращения:</b>"] + [
        f"- <i>{r['timestamp']}</i>: {html.quote(r['details'])}"
        for r in history
    ]
    await callback.message.answer("\n".join(lines))
    await callback.answer()


@router.callback_query(AdminPanelCallback.filter(F.action == "show_stats"))
async def show_stats(callback: CallbackQuery):
    admin_info = await get_admin_details(callback.from_user.id)
    stats = await get_admin_stats(admin_info["permissions"])
    text = (
        "<b>Статистика обращений</b>\n"
        f"Новое: {stats.get('new', 0)}\n"
        f"В работе: {stats.get('in_work', 0)}\n"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(AdminPanelCallback.filter(F.action == "export"))
async def export_csv(callback: CallbackQuery):
    # Простой экспорт всех жалоб в CSV и отправка как файла
    import io, csv
    from aiogram.types import FSInputFile
    from utils.db import execute

    rows = await execute("SELECT * FROM complaints ORDER BY id ASC", fetch="all") or []

    buf = io.StringIO()
    if rows:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))
    else:
        buf.write("")

    tmp_path = "export_complaints.csv"
    # Записываем в UTF-8 с BOM, чтобы Excel корректно распознал кириллицу
    with open(tmp_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(buf.getvalue())

    await callback.message.answer_document(
        FSInputFile(tmp_path),
        caption="Экспорт обращений (CSV, UTF-8-BOM)"
    )
    await callback.answer("Экспорт сформирован", show_alert=True)
