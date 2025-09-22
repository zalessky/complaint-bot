# handlers/complaint_wizard.py
import logging
from datetime import datetime
from typing import List, Union

from aiogram import F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ContentType

from keyboards.inline import (
    get_categories_keyboard,
    get_subcategories_keyboard,
    get_location_keyboard,
    confirm_complaint_keyboard,
    get_datetime_keyboard,
)
from keyboards.reply import main_menu_keyboard, request_location_keyboard
from utils.constants import CATEGORIES
from utils.db import add_complaint
from utils.dto import ComplaintDTO
from utils.validators import parse_user_datetime

logger = logging.getLogger(__name__)
router = Router()

class ComplaintWizard(StatesGroup):
    (
        choose_category,
        choose_subcategory,
        enter_route_number,
        enter_violation_time,
        enter_location,
        enter_address,
        upload_media,
        enter_description,
        confirm_complaint,
    ) = [State() for _ in range(9)]

# --- Общие хэндлеры отмены ---

@router.message(Command('cancel'))
@router.callback_query(F.data == 'cancel_complaint')
async def cmd_cancel(event: Union[Message, CallbackQuery], state: FSMContext):
    await state.clear()
    text = 'Действие отменено.'
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
    else:
        await event.answer(text, reply_markup=main_menu_keyboard())

# --- Шаг 1: Категория ---

@router.message(Command('complaint'))
@router.message(F.text == 'Подать жалобу')
async def cmd_complaint(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ComplaintWizard.choose_category)
    await message.answer(
        '<b>Шаг 1: Категория</b>\nВыберите сферу проблемы:',
        reply_markup=get_categories_keyboard(),
    )

@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ComplaintWizard.choose_category)
    await callback.message.edit_text(
        '<b>Шаг 1: Категория</b>\nВыберите сферу проблемы:',
        reply_markup=get_categories_keyboard(),
    )
    await callback.answer()

# --- Шаг 2: Подкатегория ---

@router.callback_query(F.data == 'back_to_subcategories')
async def back_to_subcategories(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    category_key = user_data.get('category_key')
    if not category_key:
        return await back_to_categories(callback, state)
    await state.set_state(ComplaintWizard.choose_subcategory)
    await callback.message.edit_text(
        f'<b>Шаг 2: Уточнение</b>\nВыбрано: {CATEGORIES[category_key]["name"]}.\nУточните суть:',
        reply_markup=get_subcategories_keyboard(category_key),
    )
    await callback.answer()

@router.callback_query(ComplaintWizard.choose_category, F.data.startswith('category_'))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_key = callback.data.split('_', 1)[1]
    await state.update_data(category_key=category_key)
    await state.set_state(ComplaintWizard.choose_subcategory)
    await callback.message.edit_text(
        f'<b>Шаг 2: Уточнение</b>\nВыбрано: {CATEGORIES[category_key]["name"]}.\nУточните суть:',
        reply_markup=get_subcategories_keyboard(category_key),
    )
    await callback.answer()

@router.callback_query(ComplaintWizard.choose_subcategory, F.data.startswith('subcategory_'))
async def process_subcategory(callback: CallbackQuery, state: FSMContext):
    subcategory_id = int(callback.data.split('_')[1])
    user_data = await state.get_data()
    category_key = user_data['category_key']
    subcategory_info = CATEGORIES[category_key]['subcategories'][subcategory_id]
    await state.update_data(
        subcategory_id=subcategory_id,
        subcategory_name=subcategory_info['name'],
    )

    # Транспорт требует номер маршрута, иначе — гео/описание
    if category_key == 'transport':
        await state.set_state(ComplaintWizard.enter_route_number)
        await callback.message.edit_text('<b>Шаг 3: Номер ТС</b>\nВведите номер маршрута или гос. номер:')
    elif subcategory_info.get('geo_required'):
        await state.set_state(ComplaintWizard.enter_location)
        await callback.message.edit_text(
            '<b>Шаг 3: Местоположение</b>\nУкажите точное место:',
            reply_markup=get_location_keyboard(),
        )
    else:
        await go_to_media_step(callback.message, state, is_edit=True)
    await callback.answer()

# --- Шаг 3/4: Номер ТС ---

@router.message(ComplaintWizard.enter_route_number, F.text)
async def process_route_number(message: Message, state: FSMContext):
    await state.update_data(route_number=message.text)
    await state.set_state(ComplaintWizard.enter_violation_time)
    await message.answer(
        '<b>Шаг 4: Время нарушения</b>\nКогда произошло нарушение?',
        reply_markup=get_datetime_keyboard(),
    )

# --- Время нарушения ---

@router.callback_query(ComplaintWizard.enter_violation_time, F.data == 'datetime_now')
async def process_datetime_now(callback: CallbackQuery, state: FSMContext):
    await state.update_data(violation_datetime=datetime.now())
    await callback.message.delete()
    await go_to_media_step(callback.message, state)
    await callback.answer()

@router.callback_query(ComplaintWizard.enter_violation_time, F.data == 'datetime_manual')
async def process_datetime_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        'Введите дату и время в формате <b>ДД.ММ ЧЧ:ММ</b> (например, 21.09 11:35):'
    )
    await callback.answer()

@router.message(ComplaintWizard.enter_violation_time, F.text)
async def process_violation_time_manual_input(message: Message, state: FSMContext):
    parsed_time = parse_user_datetime(message.text)
    if parsed_time:
        await state.update_data(violation_datetime=parsed_time)
        await go_to_media_step(message, state)
    else:
        await message.answer('Неверный формат. Пожалуйста, введите дату и время как <b>ДД.ММ ЧЧ:ММ</b>.')

# --- Геолокация / адрес ---

@router.callback_query(ComplaintWizard.enter_location, F.data == 'send_geolocation')
async def request_geolocation(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer('Нажмите кнопку ниже для отправки геолокации.', reply_markup=request_location_keyboard())
    await callback.answer()

@router.callback_query(ComplaintWizard.enter_location, F.data == 'enter_address_manually')
async def request_address_manually(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ComplaintWizard.enter_address)
    await callback.message.edit_text('Введите точный адрес (улица, дом):')
    await callback.answer()

@router.message(ComplaintWizard.enter_location, F.location)
async def process_location(message: Message, state: FSMContext):
    await state.update_data(latitude=message.location.latitude, longitude=message.location.longitude)
    await message.answer('Местоположение принято!', reply_markup=main_menu_keyboard())
    await go_to_media_step(message, state)

@router.message(ComplaintWizard.enter_address, F.text)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer('Адрес принят!')
    await go_to_media_step(message, state)

# --- Медиафайлы ---

async def go_to_media_step(message: Message, state: FSMContext, is_edit: bool = False):
    user_data = await state.get_data()
    category_key, sub_id = user_data['category_key'], user_data['subcategory_id']
    sub_info = CATEGORIES[category_key]['subcategories'][sub_id]

    step_num = 5 if category_key == 'transport' else (4 if sub_info.get('geo_required') else 3)
    text = f'<b>Шаг {step_num}: Медиафайлы</b>\n'
    if sub_info.get('photo_required'):
        text += 'Для этой категории обязательно приложите фото с гос. номером ТС.'
        reply_markup: InlineKeyboardMarkup | None = None
    else:
        text += 'Приложите до 3 фото/видео (можно пропустить).'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='skip_media')]]
        )

    await state.set_state(ComplaintWizard.upload_media)
    if is_edit:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        await message.answer(text, reply_markup=reply_markup)

@router.callback_query(ComplaintWizard.upload_media, F.data == 'skip_media')
async def skip_media_upload(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    sub_info = CATEGORIES[user_data['category_key']]['subcategories'][user_data['subcategory_id']]
    if sub_info.get('photo_required'):
        return await callback.answer('Для этой категории фото обязательно.', show_alert=True)
    await state.update_data(media_file_ids=[])
    await go_to_description_step(callback.message, state, is_edit=True)
    await callback.answer()

@router.message(ComplaintWizard.upload_media, F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}))
async def process_media_upload(message: Message, state: FSMContext):
    user_data = await state.get_data()
    media: List[str] = user_data.get('media_file_ids', [])
    if len(media) >= 3:
        return await message.answer('Уже загружено 3 файла.')

    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media.append(file_id)
    await state.update_data(media_file_ids=media)

    if len(media) < 3:
        await message.answer(
            f'Загружено {len(media)}/3. Можно добавить еще или нажать "Далее".',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Далее', callback_data='finish_media_upload')]]
            ),
        )
    else:
        await message.answer('Загружено 3/3 файла.')
        await go_to_description_step(message, state)

@router.callback_query(F.data == 'finish_media_upload')
async def finish_media_upload(callback: CallbackQuery, state: FSMContext):
    await go_to_description_step(callback.message, state, is_edit=True)
    await callback.answer()

# --- Описание ---

async def go_to_description_step(message: Message, state: FSMContext, is_edit: bool = False):
    await state.set_state(ComplaintWizard.enter_description)
    user_data = await state.get_data()
    step_num = 6 if user_data.get('category_key') == 'transport' else (5 if user_data.get('latitude') or user_data.get('address') else 4)
    text = f'<b>Шаг {step_num}: Описание</b>\nДобавьте краткое описание проблемы (по желанию):'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='skip_description')]])
    if is_edit:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        await message.answer(text, reply_markup=reply_markup)

@router.message(ComplaintWizard.enter_description, F.text)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await show_confirmation_screen(message, state)

@router.callback_query(F.data == 'skip_description')
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await show_confirmation_screen(callback.message, state, is_edit=True)
    await callback.answer()

# --- Финальное подтверждение ---

async def show_confirmation_screen(message: Message, state: FSMContext, is_edit: bool = False):
    user_data = await state.get_data()
    dto = ComplaintDTO(**user_data)
    step_num = 7 if dto.category_key == 'transport' else (6 if dto.latitude or dto.address else 5)

    lines = [
        f'<b>Финальный шаг ({step_num}/{step_num}): Подтверждение</b>',
        'Пожалуйста, проверьте данные:\n',
        f'<b>Категория:</b> {CATEGORIES[dto.category_key]["name"]}',
        f'<b>Проблема:</b> {html.quote(dto.subcategory_name)}',
    ]
    if dto.route_number:
        lines.append(f'<b>Номер ТС:</b> {html.quote(dto.route_number)}')
    if dto.violation_datetime:
        lines.append(f'<b>Время:</b> {dto.violation_datetime.strftime("%d.%m.%Y %H:%M")}')
    if dto.latitude:
        lines.append('<b>Место:</b> Отправлена геоточка')
    elif dto.address:
        lines.append(f'<b>Адрес:</b> {html.quote(dto.address)}')
    if dto.media_file_ids:
        lines.append(f'<b>Медиа:</b> {len(dto.media_file_ids)} шт.')
    if dto.description:
        lines.append(f'<b>Описание:</b> {html.quote(dto.description)}')

    await state.set_state(ComplaintWizard.confirm_complaint)
    method = message.edit_text if is_edit else message.answer
    await method('\n'.join(lines), reply_markup=confirm_complaint_keyboard())

@router.callback_query(ComplaintWizard.confirm_complaint, F.data == 'submit_complaint')
async def submit_complaint(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    dto = ComplaintDTO(**user_data, user_id=callback.from_user.id, created_at=datetime.now())
    try:
        complaint_id = await add_complaint(dto)
        await callback.message.edit_text(
            f'Спасибо! Ваше обращение принято, номер <b>#{complaint_id}</b>.',
            reply_markup=None,
        )
    except Exception as e:
        logger.error(f'Failed to save complaint: {e}', exc_info=True)
        await callback.message.edit_text('Произошла ошибка при сохранении.')
    await state.clear()
    await callback.answer()
