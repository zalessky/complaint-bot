from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import (
    get_categories_keyboard, get_subcategories_keyboard, confirm_complaint_keyboard
)
from keyboards.reply import get_cancel_keyboard, main_menu_keyboard, get_location_keyboard
from utils.constants import CATEGORIES
from utils.dto import ComplaintDTO
from utils.db import get_admin_details, save_complaint

router = Router()

class ComplaintStates(StatesGroup):
    category = State()
    subcategory = State()
    address = State()
    route_number = State()
    description = State()
    media = State()
    fio = State()
    phone = State()
    confirm = State()

async def start_complaint(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Переходим к подаче жалобы...", reply_markup=ReplyKeyboardRemove())
    await message.answer("Шаг 1: Категория\nВыберите сферу проблемы:", reply_markup=get_categories_keyboard())
    await state.set_state(ComplaintStates.category)

@router.callback_query(F.data.startswith("category_"), ComplaintStates.category)
async def select_category(callback: CallbackQuery, state: FSMContext):
    cat_key = callback.data.split("_", 1)[1]
    await state.update_data(categorykey=cat_key)
    await callback.message.edit_text(f"Выбрана категория: {CATEGORIES[cat_key]['name']}\nТеперь выберите проблему:", reply_markup=get_subcategories_keyboard(cat_key))
    await state.set_state(ComplaintStates.subcategory)
    await callback.answer()

@router.callback_query(F.data == "cancel_complaint", StateFilter(ComplaintStates))
async def cancel_complaint_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(callback.from_user.id)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Действие отменено. Вы в главном меню.", reply_markup=main_menu_keyboard(admin_info.get('role') if admin_info else None))
    await callback.answer()

@router.message(F.text == "❌ Отмена", StateFilter(ComplaintStates))
async def cancel_complaint_text(message: Message, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(message.from_user.id)
    await message.answer("Действие отменено.", reply_markup=main_menu_keyboard(admin_info.get('role') if admin_info else None))

@router.callback_query(F.data == "back_to_categories", ComplaintStates.subcategory)
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите сферу проблемы:", reply_markup=get_categories_keyboard())
    await state.set_state(ComplaintStates.category)
    await callback.answer()

@router.callback_query(F.data.startswith("subcategory_"), ComplaintStates.subcategory)
async def select_subcategory(callback: CallbackQuery, state: FSMContext):
    subcat_id = int(callback.data.split("_", 1)[1])
    data = await state.get_data()
    cat_key = data["categorykey"]
    subcat = CATEGORIES[cat_key]['subcategories'][subcat_id]
    await state.update_data(subcategoryid=subcat_id, subcategoryname=subcat['name'])

    await callback.message.delete()
    if subcat.get('route_instead_of_address'):
        await callback.message.answer(f"Выбрана проблема: {subcat['name']}\nВведите номер маршрута или госномер ТС:", reply_markup=get_cancel_keyboard())
        await state.set_state(ComplaintStates.route_number)
    else:
        geo_required = subcat.get('geo_required', False)
        await callback.message.answer(
            f"Выбрана проблема: {subcat['name']}\nВведите адрес или отправьте геолокацию:",
            reply_markup=get_location_keyboard(geo_required)
        )
        await state.set_state(ComplaintStates.address)
    await callback.answer()

# --- Back Navigation Handlers (Reply buttons) ---
@router.message(F.text == "⬅️ Назад", StateFilter(ComplaintStates))
async def back_handler_complaint(message: Message, state: FSMContext):
    current_state_str = await state.get_state()
    data = await state.get_data()
    
    state_map = {
        ComplaintStates.confirm: {
            'prev_state': ComplaintStates.phone,
            'message': "Возврат к шагу ввода телефона.",
            'keyboard': get_cancel_keyboard(request_contact=True)
        },
        ComplaintStates.phone: {
            'prev_state': ComplaintStates.fio,
            'message': "Возврат к шагу ввода ФИО.",
            'keyboard': get_cancel_keyboard()
        },
        ComplaintStates.fio: {
            'prev_state': ComplaintStates.media,
            'message': "Возврат к шагу добавления фото.",
            'keyboard': get_cancel_keyboard(finish_photo=True)
        },
        ComplaintStates.media: {
            'prev_state': ComplaintStates.description,
            'message': "Возврат к шагу описания проблемы.",
            'keyboard': get_cancel_keyboard()
        },
        ComplaintStates.description: {
            'prev_state_logic': True
        },
        ComplaintStates.address: {
            'prev_state': ComplaintStates.subcategory,
            'message': "Возврат к выбору подкатегории."
        },
        ComplaintStates.route_number: {
            'prev_state': ComplaintStates.subcategory,
            'message': "Возврат к выбору подкатегории."
        },
    }

    current_state_enum = ComplaintStates(current_state_str)
    if current_state_enum in state_map:
        info = state_map[current_state_enum]
        if info.get('prev_state_logic'):
            subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
            if subcat.get('route_instead_of_address'):
                await state.set_state(ComplaintStates.route_number)
                await message.answer(f"Выбрана проблема: {subcat['name']}\nВозврат к шагу ввода номера маршрута.", reply_markup=get_cancel_keyboard())
            else:
                await state.set_state(ComplaintStates.address)
                await message.answer(f"Выбрана проблема: {subcat['name']}\nВозврат к шагу ввода адреса.", reply_markup=get_location_keyboard(subcat.get('geo_required', False)))
        else:
            await state.set_state(info['prev_state'])
            await message.answer(info['message'], reply_markup=info.get('keyboard', ReplyKeyboardRemove()))
            if info['prev_state'] == ComplaintStates.subcategory:
                await message.answer(f"Выберите проблему:", reply_markup=get_subcategories_keyboard(data['categorykey']))
    else:
        await message.answer("Невозможно вернуться назад или нет предыдущего шага.")


# --- Data Entry Handlers ---
@router.message(ComplaintStates.route_number, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_route_number(message: Message, state: FSMContext):
    await state.update_data(routenumber=message.text.strip(), address=None)
    data = await state.get_data()
    subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
    await message.answer(f"Проблема: {subcat['name']}\nМесто/Маршрут: {data.get('routenumber', '-')}\nОпишите проблему:", reply_markup=get_cancel_keyboard())
    await state.set_state(ComplaintStates.description)

@router.message(ComplaintStates.address, F.location)
async def set_address_location(message: Message, state: FSMContext):
    await state.update_data(address=f"{message.location.latitude}, {message.location.longitude}", routenumber=None)
    data = await state.get_data()
    subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
    await message.answer(f"Проблема: {subcat['name']}\nАдрес: {data.get('address', '-')}\nОпишите проблему:", reply_markup=get_cancel_keyboard())
    await state.set_state(ComplaintStates.description)

@router.message(ComplaintStates.address, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_address_text(message: Message, state: FSMContext):
    addr = message.text.strip()
    if not addr:
        await message.answer("Адрес обязателен!")
        return
    await state.update_data(address=addr, routenumber=None)
    data = await state.get_data()
    subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
    await message.answer(f"Проблема: {subcat['name']}\nАдрес: {data.get('address', '-')}\nОпишите проблему:", reply_markup=get_cancel_keyboard())
    await state.set_state(ComplaintStates.description)

@router.message(ComplaintStates.description, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    if not desc:
        await message.answer("Описание жалобы обязательно!", reply_markup=get_cancel_keyboard())
        return
    await state.update_data(description=desc)
    data = await state.get_data()
    subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
    await message.answer(
        f"Категория: {CATEGORIES[data['categorykey']]['name']}\nПроблема: {subcat['name']}\nОписание: {data.get('description', '-')}\nЕсли есть фото (до 3 шт.), отправьте их. Когда закончите, нажмите кнопку.", 
        reply_markup=get_cancel_keyboard(finish_photo=True)
    )
    await state.update_data(mediafileids=[])
    await state.set_state(ComplaintStates.media)

@router.message(ComplaintStates.media, F.photo)
async def set_media_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    media_ids = data.get('mediafileids', [])
    
    if len(media_ids) >= 3:
        await message.answer("Вы уже добавили 3 фото. Нажмите 'Завершить добавление фото'.")
        return

    media_ids.append(message.photo[-1].file_id)
    await state.update_data(mediafileids=media_ids)
    
    if len(media_ids) == 3:
        await message.answer("Достигнут лимит в 3 фото. Перехожу к следующему шагу.", reply_markup=ReplyKeyboardRemove())
        await message.answer("Теперь укажите Ваши ФИО:", reply_markup=get_cancel_keyboard())
        await state.set_state(ComplaintStates.fio)
    else:
        if not message.media_group_id:
            await message.answer(f"Фото добавлено ({len(media_ids)}/3). Отправьте еще или нажмите 'Завершить добавление фото'.")

@router.message(ComplaintStates.media, F.text.lower() == "завершить добавление фото")
async def set_media_skip(message: Message, state: FSMContext):
    await message.answer("Теперь укажите Ваши ФИО:", reply_markup=get_cancel_keyboard())
    await state.set_state(ComplaintStates.fio)

@router.message(ComplaintStates.fio, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    if not fio or len(fio.split()) < 2:
        await message.answer("Пожалуйста, укажите хотя бы Фамилию и Имя.")
        return
    await state.update_data(fio=fio)
    data = await state.get_data()
    await message.answer(
        f"ФИО: {data.get('fio', '-')}\nОтправьте номер телефона:", 
        reply_markup=get_cancel_keyboard(request_contact=True)
    )
    await state.set_state(ComplaintStates.phone)

@router.message(ComplaintStates.phone, F.contact)
async def set_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await show_confirm(message, state)

@router.message(ComplaintStates.phone, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not (phone.replace("+", "").isdigit() and len(phone) > 5):
        await message.answer("Введите корректный номер телефона или отправьте из Telegram.")
        return
    await state.update_data(phone=phone)
    await show_confirm(message, state)

async def show_confirm(message, state):
    data = await state.get_data()
    subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
    photo_ids = data.get('mediafileids', [])
    address_or_route = data.get('address') or data.get('routenumber')
    
    card = (f"<b>Финальный шаг: Подтверждение</b>\n"
            f"Проверьте все данные:\n"
            f"\n<b>Категория:</b> {CATEGORIES[data['categorykey']]['name']}"
            f"\n<b>Проблема:</b> {subcat['name']}"
            f"\n<b>Место/Маршрут:</b> {address_or_route or '-'}"
            f"\n<b>Описание:</b> {data.get('description','-')}"
            f"\n<b>ФИО:</b> {data.get('fio','-')}"
            f"\n<b>Телефон:</b> {data.get('phone','-')}" )
    
    await message.answer("Пожалуйста, подождите...", reply_markup=ReplyKeyboardRemove())

    if photo_ids:
        media = [InputMediaPhoto(media=pid) for pid in photo_ids]
        await message.answer_media_group(media)
    
    await message.answer(card, parse_mode="HTML", reply_markup=confirm_complaint_keyboard())
    await state.set_state(ComplaintStates.confirm)

@router.callback_query(F.data == "submit_complaint", ComplaintStates.confirm)
async def submit_complaint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dto = ComplaintDTO(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        **data
    )
    await save_complaint(dto)
            
    await callback.message.edit_reply_markup(reply_markup=None) # Remove inline buttons after submission
    await callback.message.answer("Ваше обращение принято! Спасибо.", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    admin_info = await get_admin_details(callback.from_user.id)
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard(admin_info.get('role') if admin_info else None))
    await callback.answer()
