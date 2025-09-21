import asyncio
import csv
import io
import logging
from typing import List

from aiogram import F, Router, html
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, BufferedInputFile

from middlewares.access_control import IsAdmin
from utils.db import (
    get_stats,
    get_last_complaints,
    get_all_complaints_for_export,
    update_complaint_status,
    ComplaintStatus,
)

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Handles the /stats command. Shows complaint statistics."""
    stats = await get_stats()
    if not stats or not stats.get("total_all_time", 0):
        await message.answer("Жалоб пока нет.")
        return

    response_text = [
        "<b>Статистика по жалобам:</b>\n",
        f"Всего жалоб за сегодня: <b>{stats['total_today']}</b>",
        f"Всего жалоб за все время: <b>{stats['total_all_time']}</b>\n",
        "<b>По типам (всего):</b>"
    ]
    
    for type_stat in stats.get("by_type", []):
        line = f"- {html.quote(type_stat['complaint_type_name'])}: <b>{type_stat['count']}</b>"
        response_text.append(line)
    
    await message.answer("\n".join(response_text))


@router.message(Command("last"))
async def cmd_last(message: Message, command: CommandObject) -> None:
    """Handles the /last command. Shows the last N complaints with media."""
    try:
        limit = int(command.args) if command.args and command.args.isdigit() else 5
        if not (1 <= limit <= 50):
            raise ValueError("Limit must be between 1 and 50.")
    except (ValueError, TypeError):
        await message.answer("Некорректное число. Используйте <code>/last N</code>, где N от 1 до 50.")
        return

    complaints = await get_last_complaints(limit)
    if not complaints:
        await message.answer("Жалоб пока нет.")
        return

    await message.answer(f"<b>Последние {len(complaints)} жалоб:</b>")
    for complaint in complaints:
        text = (
            f"<b>Жалоба #{complaint['id']}</b> от {complaint['created_at']}\n"
            f"<b>Статус:</b> {complaint['status']}\n"
            f"<b>Тип:</b> {html.quote(complaint['complaint_type_name'])}\n"
            f"<b>Номер ТС:</b> {html.quote(complaint['route_number'])}"
        )
        await message.answer(text)

        # Send media if available
        if complaint.get('media_file_ids'):
            media_ids = complaint['media_file_ids'].split(',')
            await message.answer(f"Прикрепленные медиафайлы ({len(media_ids)} шт.):")
            for file_id in media_ids:
                # Telegram can often send by file_id without knowing the type,
                # but for robustness, one might store media type in DB.
                # Here we try sending as photo, which works for both photo and video file_ids in many cases.
                try:
                    await message.answer_photo(file_id)
                except Exception:
                    try:
                        await message.answer_video(file_id)
                    except Exception as e:
                        logger.warning(f"Could not send media with file_id {file_id} for complaint {complaint['id']}: {e}")
            
        await asyncio.sleep(0.3) # Avoid hitting rate limits


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    """Handles the /export command. Exports all complaints to a CSV file."""
    complaints = await get_all_complaints_for_export()
    if not complaints:
        await message.answer("Нет жалоб для экспорта.")
        return

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "User_ID", "Status", "Created_At", "Violation_Datetime", 
        "Complaint_Type", "Other_Description", "Route_Number", "Direction", "Media_File_IDs"
    ])
    
    # Write data
    for row in complaints:
        writer.writerow([
            row['id'], row['user_id'], row['status'], row['created_at'], row['violation_datetime'],
            row['complaint_type_name'], row['other_description'], row['route_number'], 
            row['direction'], row.get('media_file_ids', '')
        ])
    
    output.seek(0)
    # Use utf-8-sig encoding to make Excel happy
    csv_file = BufferedInputFile(output.getvalue().encode('utf-8-sig'), filename="complaints_export.csv")
    await message.answer_document(csv_file, caption="Экспорт всех жалоб в формате CSV.")


@router.message(Command("setstatus"))
async def cmd_set_status(message: Message, command: CommandObject) -> None:
    """Handles the /setstatus command. Sets the status of a complaint."""
    args = command.args
    if not args or len(args.split()) != 2:
        await message.answer("Используйте формат: <code>/setstatus &lt;ID&gt; &lt;статус&gt;</code>\nСтатусы: ok, reject, in_work")
        return

    complaint_id_str, new_status_str = args.split()
    
    if not complaint_id_str.isdigit():
        await message.answer("ID жалобы должен быть числом.")
        return

    complaint_id = int(complaint_id_str)
    
    try:
        new_status = ComplaintStatus(new_status_str.lower())
    except ValueError:
        valid_statuses = ", ".join([s.value for s in ComplaintStatus])
        await message.answer(f"Неверный статус. Допустимые значения: {valid_statuses}")
        return

    success = await update_complaint_status(complaint_id, new_status)
    if success:
        await message.answer(f"Статус жалобы #{complaint_id} изменен на <b>{new_status.value}</b>.")
        logger.info("Admin %s changed status of complaint %d to %s", message.from_user.id, complaint_id, new_status.value)
    else:
        await message.answer(f"Жалоба с ID #{complaint_id} не найдена.")
