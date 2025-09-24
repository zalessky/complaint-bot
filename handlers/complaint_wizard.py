from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from aiogram.filters.state import State, StatesGroup
from keyboards.inline import get_categories_keyboard, get_subcategories_keyboard, confirm_complaint_keyboard
from utils.constants import CATEGORIES
from utils.dto import ComplaintDTO
from keyboards.reply import main_menu_keyboard
from utils.db import get_admin_details, save_complaint

router = Router()

class ComplaintStates(StatesGroup):
    category = State()
    subcategory = State()
    address = State()
    description = State()
    media = State()
    fio = State()
    phone = State()
    confirm = State()

@router.message(F.text.lower().in_(["подать жалобу", "/complaint"]))
async def start_complaint(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Шаг 1: Категория\nВыберите сферу проблемы:", reply_markup=get_categories_keyboard())
    await state.set_state(ComplaintStates.category)

@router.callback_query(F.data.startswith("category_"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    cat_key = callback.data.split("_", 1)[1]
    await state.update_data(categorykey=cat_key)
    await callback.message.answer(f"Выбрана категория: {CATEGORIES[cat_key]['name']}\nТеперь выберите проблему:", reply_markup=get_subcategories_keyboard(cat_key))
    await state.set_state(ComplaintStates.subcategory)
    await callback.answer()

@router.callback_query(F.data == "cancel_complaint")
async def cancel_complaint(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(callback.from_user.id)
    is_admin = admin_info and admin_info.get('role','') in ('admin','superadmin')
    await callback.message.answer("Действие отменено.", reply_markup=main_menu_keyboard(is_admin))
    await callback.answer()

@router.callback_query(F.data.startswith("subcategory_"))
async def select_subcategory(callback: CallbackQuery, state: FSMContext):
    subcat_id = int(callback.data.split("_", 1)[1])
    data = await state.get_data()
    cat_key = data["categorykey"]
    subcat = CATEGORIES[cat_key]['subcategories'][subcat_id]
    await state.update_data(subcategoryid=subcat_id, subcategoryname=subcat['name'])
    await callback.message.answer("Введите адрес (или воспользуйтесь геолокацией):")
    await state.set_state(ComplaintStates.address)
    await callback.answer()

@router.message(ComplaintStates.address)
async def set_address(message: Message, state: FSMContext):
    addr = message.text.strip()
    if not addr:
        await message.answer("Адрес обязателен!")
        return
    await state.update_data(address=addr)
    await message.answer("Опишите проблему (обязательно):")
    await state.set_state(ComplaintStates.description)

@router.message(ComplaintStates.description)
async def set_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    if not desc:
        await message.answer("Описание жалобы обязательно!")
        return
    await state.update_data(description=desc)
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить фото")]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer('Если есть фото (до 3 шт.), отправьте по одному, либо нажмите "Пропустить фото".', reply_markup=keyboard)
    await state.update_data(mediafileids=[])
    await state.set_state(ComplaintStates.media)

@router.message(ComplaintStates.media)
async def set_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_ids = data.get('mediafileids', [])
    if message.photo:
        media_ids.append(message.photo[-1].file_id)
        await state.update_data(mediafileids=media_ids)
        if len(media_ids) < 3:
            await message.answer(f"Фото добавлено ({len(media_ids)}/3). Отправьте еще фото или нажмите 'Пропустить фото'.")
            return
    if message.text and 'пропустить' in message.text.lower():
        await message.answer("Теперь укажите ФИО:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True, selective=True))
        await state.set_state(ComplaintStates.fio)
    elif len(media_ids) == 3:
        await message.answer("Достигнут лимит 3 фото. Теперь укажите ФИО:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True, selective=True))
        await state.set_state(ComplaintStates.fio)

@router.message(ComplaintStates.fio)
async def set_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    if not fio or len(fio.split()) < 2:
        await message.answer("Пожалуйста, укажите Фамилию Имя Отчество.")
        return
    await state.update_data(fio=fio)
    contact_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Отправьте номер телефона — либо поделитесь из профиля Telegram, либо введите вручную:", reply_markup=contact_keyboard)
    await state.set_state(ComplaintStates.phone)

@router.message(ComplaintStates.phone)
async def set_phone(message: Message, state: FSMContext):
    phone = None
    if hasattr(message, 'contact') and message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
    if not phone or len(phone) < 5:
        await message.answer("Введите корректный номер телефона или отправьте из Telegram.")
        return
    await state.update_data(phone=phone)
    await show_confirm(message, state)

async def show_confirm(message, state):
    data = await state.get_data()
    subcat = CATEGORIES[data['categorykey']]['subcategories'][data['subcategoryid']]
    photo_ids = data.get('mediafileids', [])
    card = (f"<b>Финальный шаг: Подтверждение</b>\n"
            f"Проверьте все данные:\n"
            f"\n<b>Категория:</b> {CATEGORIES[data['categorykey']]['name']}"
            f"\n<b>Проблема:</b> {subcat['name']}"
            f"\n<b>Адрес:</b> {data.get('address','-')}"
            f"\n<b>Описание:</b> {data.get('description','-')}"
            f"\n<b>ФИО:</b> {data.get('fio','-')}"
            f"\n<b>Телефон:</b> {data.get('phone','-')}" )
    if photo_ids:
        media = [InputMediaPhoto(media=pid) for pid in photo_ids]
        if len(media) == 1:
            await message.answer_photo(media[0].media, caption=card, parse_mode="HTML", reply_markup=confirm_complaint_keyboard())
        else:
            await message.answer_media_group(media)
            await message.answer(card, parse_mode="HTML", reply_markup=confirm_complaint_keyboard())
    else:
        await message.answer(card, parse_mode="HTML", reply_markup=confirm_complaint_keyboard())
    await state.set_state(ComplaintStates.confirm)

@router.callback_query(F.data == "submit_complaint")
async def submit_complaint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dto = ComplaintDTO(**data)
    await save_complaint(dto)
    await callback.message.answer("Ваше обращение принято! Наши специалисты свяжутся с вами при необходимости.")
    await state.clear()
    from utils.db import get_admin_details
    admin_info = await get_admin_details(callback.from_user.id)
    is_admin = admin_info and admin_info.get('role','') in ('admin','superadmin')
    await callback.message.answer("Меню", reply_markup=main_menu_keyboard(is_admin))
    await callback.answer()
