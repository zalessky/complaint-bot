# engels-transport-bot/handlers/complaint_wizard.py

import logging
from datetime import datetime, timedelta
from typing import Union, List

from aiogram import F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ContentType,
)
from aiogram.utils.markdown import hbold

from keyboards.inline import (
    confirm_complaint_keyboard,
    complaint_types_keyboard,
    get_datetime_keyboard,
)
from keyboards.reply import main_menu_keyboard
from utils.db import add_complaint
from utils.dto import ComplaintDTO
from utils.validators import validate_datetime, is_valid_route_or_plate, is_valid_direction_text
from utils.constants import COMPLAINT_TYPES  # <-- ИМПОРТИРУЕМ ОТСЮДА

logger = logging.getLogger(__name__)
router = Router()


class ComplaintWizard(StatesGroup):
    """FSM states for the complaint submission wizard."""
    choose_type = State()
    other_type_description = State()
    enter_route_number = State()
    enter_direction = State()
    enter_datetime = State()
    upload_media = State()
    confirm_complaint = State()


# --- Handlers for starting and canceling the wizard ---

@router.message(Command("complaint"))
@router.message(F.text == "Подать жалобу")
async def cmd_complaint(message: Message, state: FSMContext) -> None:
    """Starts the complaint wizard."""
    logger.info("User %s started complaint wizard.", message.from_user.id)
    await state.clear()
    await state.set_state(ComplaintWizard.choose_type)
    await message.answer(
        "<b>Шаг 1/6: Тип нарушения</b>\\nВыберите тип нарушения из списка.",
        reply_markup=complaint_types_keyboard(),
    )


@router.message(Command("cancel"))
@router.callback_query(F.data == "cancel_complaint")
async def cmd_cancel(event: Union[Message, CallbackQuery], state: FSMContext) -> None:
    """Handles the /cancel command and cancel button clicks."""
    await state.clear()
    response_text = "Действие отменено. Вы можете начать заново с команды /complaint."
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(response_text)
        await event.answer()
    else:
        await event.answer(response_text, reply_markup=main_menu_keyboard())
    logger.info("User %s canceled the wizard.", event.from_user.id)


# --- Step-by-step wizard handlers ---

@router.callback_query(ComplaintWizard.choose_type, F.data.startswith("complaint_type_"))
async def process_complaint_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Handles the selection of the complaint type."""
    type_id = int(callback.data.split("_")[2])
    type_name = COMPLAINT_TYPES.get(type_id, "Неизвестный тип")
    await state.update_data(complaint_type_id=type_id, complaint_type_name=type_name)
    logger.info("User %s selected type %d: %s", callback.from_user.id, type_id, type_name)

    if type_id == 14:  # "Other"
        await state.set_state(ComplaintWizard.other_type_description)
        await callback.message.edit_text(
            "<b>Шаг 1.1/6: Описание</b>\\nОпишите суть нарушения (до 200 символов):"
        )
    else:
        await state.set_state(ComplaintWizard.enter_route_number)
        await callback.message.edit_text(
            "<b>Шаг 2/6: Номер ТС</b>\\nВведите номер маршрута или гос-номер ТС (например, '28', 'А123ВВ'):"
        )
    await callback.answer()


@router.message(ComplaintWizard.other_type_description, F.text)
async def process_other_type_description(message: Message, state: FSMContext) -> None:
    """Handles the description for the 'Other' complaint type."""
    if not message.text or len(message.text) > 200:
        await message.answer("Описание не должно быть пустым и не может превышать 200 символов. Попробуйте еще раз.")
        return

    await state.update_data(other_description=message.text.strip())
    await state.set_state(ComplaintWizard.enter_route_number)
    await message.answer(
        "<b>Шаг 2/6: Номер ТС</b>\\nВведите номер маршрута или гос-номер ТС (например, '28', 'А123ВВ'):"
    )


@router.message(ComplaintWizard.enter_route_number, F.text)
async def process_route_number(message: Message, state: FSMContext) -> None:
    """Handles the route/plate number input."""
    if not is_valid_route_or_plate(message.text.strip()):
        await message.answer("Некорректный формат. Введите номер маршрута или гос-номер ТС (например, '28', 'А123ВВ 164').")
        return

    await state.update_data(route_number=message.text.strip())
    await state.set_state(ComplaintWizard.enter_direction)
    await message.answer("<b>Шаг 3/6: Направление</b>\\nВведите направление движения (например, 'из центра', 'в пос. Юбилейный'):")


@router.message(ComplaintWizard.enter_direction, F.text)
async def process_direction(message: Message, state: FSMContext) -> None:
    """Handles the direction input."""
    if not is_valid_direction_text(message.text.strip()):
        await message.answer("Направление не должно быть пустым. Пожалуйста, введите направление движения.")
        return

    await state.update_data(direction=message.text.strip())
    await state.set_state(ComplaintWizard.enter_datetime)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    await message.answer(
        f"<b>Шаг 4/6: Дата и время</b>\\nНарушение произошло сейчас ({hbold(now_str)})?",
        reply_markup=get_datetime_keyboard(now_str),
    )


@router.callback_query(ComplaintWizard.enter_datetime, F.data.startswith("datetime_confirm_"))
async def confirm_current_datetime(callback: CallbackQuery, state: FSMContext) -> None:
    """Handles the confirmation of the current datetime."""
    dt_str = callback.data.split("_", 2)[2]
    try:
        violation_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        await state.update_data(violation_datetime=violation_dt)
        await state.set_state(ComplaintWizard.upload_media)
        await callback.message.edit_text(
            "<b>Шаг 5/6: Медиафайлы</b>\\nЗагрузите до 3 фото/видео или пропустите этот шаг.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Пропустить", callback_data="skip_media")],
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_complaint")]
            ])
        )
    except ValueError:
        await callback.message.edit_text("Ошибка обработки времени. Попробуйте ввести вручную.")
    await callback.answer()

@router.callback_query(ComplaintWizard.enter_datetime, F.data == "enter_manual_datetime")
async def enter_manual_datetime(callback: CallbackQuery, state: FSMContext) -> None:
    """Handles the manual datetime input request."""
    await callback.message.edit_text("Введите дату и время в формате <b>ГГГГ-ММ-ДД ЧЧ:ММ</b> (например, '2024-02-20 14:30'):")
    await callback.answer()

@router.message(ComplaintWizard.enter_datetime, F.text)
async def process_datetime_input(message: Message, state: FSMContext) -> None:
    """Handles manual datetime input."""
    dt_str = message.text.strip()
    if not validate_datetime(dt_str):
        await message.answer("Некорректный формат. Введите дату и время как <b>ГГГГ-ММ-ДД ЧЧ:ММ</b>.")
        return

    violation_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    if violation_dt > datetime.now() + timedelta(minutes=5):
        await message.answer("Дата нарушения не может быть в будущем. Пожалуйста, проверьте ввод.")
        return

    await state.update_data(violation_datetime=violation_dt)
    await state.set_state(ComplaintWizard.upload_media)
    await message.answer(
        "<b>Шаг 5/6: Медиафайлы</b>\\nЗагрузите до 3 фото/видео или пропустите этот шаг.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_media")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_complaint")]
        ])
    )


@router.callback_query(ComplaintWizard.upload_media, F.data == "skip_media")
async def skip_media_upload(callback: CallbackQuery, state: FSMContext) -> None:
    """Skips the media upload step."""
    await state.update_data(media_file_ids=[])
    await callback.message.edit_text("Загрузка медиа пропущена.")
    await show_confirmation_screen(callback.message, state, is_edit=True)
    await callback.answer()

@router.message(ComplaintWizard.upload_media, F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}))
async def process_media_upload(message: Message, state: FSMContext) -> None:
    """Handles media file uploads."""
    user_data = await state.get_data()
    media_file_ids: List[str] = user_data.get("media_file_ids", [])

    if len(media_file_ids) >= 3:
        await message.answer("Вы уже загрузили 3 файла. Нажмите 'Подтвердить' для завершения.")
        return

    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media_file_ids.append(file_id)
    await state.update_data(media_file_ids=media_file_ids)
    logger.info("User %s uploaded media. Total: %d", message.from_user.id, len(media_file_ids))

    if len(media_file_ids) < 3:
        await message.answer(
            f"Загружено {len(media_file_ids)}/3. Можете добавить еще или нажать 'Подтвердить'.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Подтвердить и завершить", callback_data="confirm_media_upload")],
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_complaint")]
            ])
        )
    else:
        await message.answer("Загружено максимальное количество файлов (3).")
        await show_confirmation_screen(message, state)

@router.message(ComplaintWizard.upload_media)
async def process_unsupported_media(message: Message) -> None:
    """Handles unsupported content types during media upload."""
    await message.answer("Пожалуйста, загрузите только фото или видео.")

@router.callback_query(F.data == "confirm_media_upload")
async def confirm_media_upload(callback: CallbackQuery, state: FSMContext) -> None:
    """Handles confirmation after media uploads."""
    await show_confirmation_screen(callback.message, state, is_edit=True)
    await callback.answer()


# --- Confirmation and saving ---

async def show_confirmation_screen(message: Message, state: FSMContext, is_edit: bool = False) -> None:
    """Displays the confirmation screen with all the data."""
    user_data = await state.get_data()
    dto = ComplaintDTO(**user_data)
    
    # Format the confirmation text using a list and join for clarity
    text_lines = [
        "<b>Шаг 6/6: Подтверждение</b>",
        "Пожалуйста, проверьте все данные перед отправкой:\n",
        f"<b>Тип нарушения:</b> {html.quote(dto.complaint_type_name)}"
    ]
    if dto.other_description:
        text_lines.append(f"<b>Описание:</b> {html.quote(dto.other_description)}")
    
    text_lines.extend([
        f"<b>Номер ТС:</b> {html.quote(dto.route_number)}",
        f"<b>Направление:</b> {html.quote(dto.direction)}",
        f"<b>Дата и время:</b> {dto.violation_datetime.strftime('%Y-%m-%d %H:%M')}",
        f"<b>Прикреплено медиа:</b> {'Да' if dto.media_file_ids else 'Нет'} ({len(dto.media_file_ids)} шт.)"
    ])
    
    confirmation_text = "\n".join(text_lines)
    
    await state.set_state(ComplaintWizard.confirm_complaint)
    method = message.edit_text if is_edit else message.answer
    await method(confirmation_text, reply_markup=confirm_complaint_keyboard())

@router.callback_query(ComplaintWizard.confirm_complaint, F.data == "submit_complaint")
async def submit_complaint(callback: CallbackQuery, state: FSMContext) -> None:
    """Saves the complaint to the database."""
    user_data = await state.get_data()
    dto = ComplaintDTO(**user_data)
    dto.user_id = callback.from_user.id
    
    try:
        complaint_id = await add_complaint(dto)
        logger.info("User %s submitted a new complaint with ID %d.", dto.user_id, complaint_id)
        await callback.message.edit_text(
            f"Спасибо! Ваша жалоба принята и зарегистрирована под номером <b>#{complaint_id}</b>.",
            reply_markup=None
        )
    except Exception as e:
        logger.error("Failed to save complaint for user %s: %s", dto.user_id, e, exc_info=True)
        await callback.message.edit_text("Произошла ошибка при сохранении вашей жалобы. Пожалуйста, попробуйте позже.")
    
    await state.clear()
    await callback.answer()
