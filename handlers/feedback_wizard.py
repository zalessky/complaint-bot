from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from keyboards.inline import confirm_complaint_keyboard, get_feedback_type_keyboard
from keyboards.reply import get_cancel_keyboard, main_menu_keyboard
from utils.dto import ComplaintDTO
from utils.db import get_admin_details, save_complaint
from utils.constants import CATEGORIES # Import CATEGORIES to use for subcategory names

router = Router()

class FeedbackStates(StatesGroup):
    type_selection = State()
    recipient = State() # For gratitude
    description = State()
    media = State()
    fio = State()
    phone = State()
    confirm = State()

async def start_feedback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите тип вашего обращения:", reply_markup=get_feedback_type_keyboard())
    await state.set_state(FeedbackStates.type_selection)

@router.callback_query(F.data.startswith("feedback:"), FeedbackStates.type_selection)
async def process_feedback_type(callback: CallbackQuery, state: FSMContext):
    feedback_type = callback.data.split(':')[1]
    await state.update_data(feedback_type=feedback_type)
    await callback.message.delete()

    if feedback_type == 'gratitude':
        await state.set_state(FeedbackStates.recipient)
        await callback.message.answer("Кому вы хотите выразить благодарность? (например, 'водителю автобуса №53' или 'МУП Свет')", reply_markup=get_cancel_keyboard())
    elif feedback_type in ['suggestion', 'bug_report']:
        prompt = "Опишите ваше предложение по улучшению:" if feedback_type == 'suggestion' else "Опишите ошибку, с которой вы столкнулись:"
        await state.set_state(FeedbackStates.description)
        await callback.message.answer(prompt, reply_markup=get_cancel_keyboard())
    await callback.answer()

@router.message(F.text == "❌ Отмена", StateFilter(FeedbackStates))
async def cancel_feedback_text(message: Message, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(message.from_user.id)
    await message.answer("Действие отменено.", reply_markup=main_menu_keyboard(admin_info.get('role') if admin_info else None))

@router.message(F.text == "⬅️ Назад", StateFilter(FeedbackStates))
async def back_handler_feedback(message: Message, state: FSMContext):
    current_state_str = await state.get_state()
    data = await state.get_data()
    feedback_type = data.get('feedback_type')

    state_map = {
        FeedbackStates.confirm: {
            'prev_state': FeedbackStates.phone,
            'message': "Возврат к шагу ввода телефона.",
            'keyboard': get_cancel_keyboard(request_contact=True)
        },
        FeedbackStates.phone: {
            'prev_state': FeedbackStates.fio,
            'message': "Возврат к шагу ввода ФИО.",
            'keyboard': get_cancel_keyboard()
        },
        FeedbackStates.fio: {
            'prev_state': FeedbackStates.media if feedback_type == 'gratitude' else FeedbackStates.description,
            'message': "Возврат к предыдущему шагу.",
            'keyboard': get_cancel_keyboard(finish_photo=True) if feedback_type == 'gratitude' else get_cancel_keyboard()
        },
        FeedbackStates.media: {
            'prev_state': FeedbackStates.description,
            'message': "Возврат к шагу описания. ",
            'keyboard': get_cancel_keyboard()
        },
        FeedbackStates.description: {
            'prev_state': FeedbackStates.recipient if feedback_type == 'gratitude' else FeedbackStates.type_selection,
            'message': "Возврат к предыдущему шагу.",
            'keyboard': get_cancel_keyboard() if feedback_type == 'gratitude' else get_feedback_type_keyboard()
        },
        FeedbackStates.recipient: {
            'prev_state': FeedbackStates.type_selection,
            'message': "Возврат к выбору типа обращения.",
            'keyboard': get_feedback_type_keyboard()
        },
    }

    current_state_enum = FeedbackStates(current_state_str)
    if current_state_enum in state_map:
        info = state_map[current_state_enum]
        await state.set_state(info['prev_state'])
        if isinstance(info['keyboard'], ReplyKeyboardMarkup):
            await message.answer(info['message'], reply_markup=info['keyboard'])
        else:
            await message.answer(info['message'], reply_markup=ReplyKeyboardRemove())
            await message.answer(info['message'], reply_markup=info['keyboard'])
    else:
        await message.answer("Невозможно вернуться назад или нет предыдущего шага.")


@router.message(FeedbackStates.recipient, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_recipient(message: Message, state: FSMContext):
    await state.update_data(routenumber=message.text.strip(), address=None)
    data = await state.get_data()
    await message.answer(
        f"Кому: {data.get('routenumber', '-')}\nОпишите, за что вы благодарны:", 
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(FeedbackStates.description)

@router.message(FeedbackStates.description, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    data = await state.get_data()
    if data['feedback_type'] == 'gratitude':
        recipient_text = f"Кому: {data.get('routenumber', '-')}\n" if data.get('routenumber') else ""
        await message.answer(
            f"{recipient_text}Текст: {data.get('description', '-')}\nЕсли хотите, приложите фото (до 3 шт.), или нажмите кнопку.", 
            reply_markup=get_cancel_keyboard(finish_photo=True)
        )
        await state.set_state(FeedbackStates.media)
    else:
        await message.answer(
            f"Текст: {data.get('description', '-')}\nТеперь укажите Ваши ФИО:", 
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(FeedbackStates.fio)

@router.message(FeedbackStates.media, F.photo)
async def set_media_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    media_ids = data.get('mediafileids', [])
    if len(media_ids) < 3:
        media_ids.append(message.photo[-1].file_id)
        await state.update_data(mediafileids=media_ids)
        if len(media_ids) == 3:
            await message.answer("Достигнут лимит в 3 фото.", reply_markup=ReplyKeyboardRemove())
            await message.answer("Теперь укажите Ваши ФИО:", reply_markup=get_cancel_keyboard())
            await state.set_state(FeedbackStates.fio)
        else:
            if not message.media_group_id:
                await message.answer(f"Фото добавлено ({len(media_ids)}/3). Отправьте еще или нажмите 'Завершить добавление фото'.")

@router.message(FeedbackStates.media, F.text.lower() == "завершить добавление фото")
async def set_media_skip(message: Message, state: FSMContext):
    await message.answer("Теперь укажите Ваши ФИО:", reply_markup=get_cancel_keyboard())
    await state.set_state(FeedbackStates.fio)

@router.message(FeedbackStates.fio, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, укажите Ваше имя.")
        return
    await state.update_data(fio=fio)
    data = await state.get_data()
    await message.answer(
        f"ФИО: {data.get('fio', '-')}\nОставьте номер телефона для связи:", 
        reply_markup=get_cancel_keyboard(request_contact=True)
    )
    await state.set_state(FeedbackStates.phone)

@router.message(FeedbackStates.phone, F.contact)
async def set_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await show_feedback_confirm(message, state)

@router.message(FeedbackStates.phone, F.text.not_in(['⬅️ Назад', '❌ Отмена']))
async def set_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not (phone.replace("+", "").isdigit() and len(phone) > 5):
        await message.answer("Введите корректный номер телефона.")
        return
    await state.update_data(phone=phone)
    await show_feedback_confirm(message, state)

async def show_feedback_confirm(message, state):
    data = await state.get_data()
    feedback_type = data['feedback_type']
    
    title_map = {
        'gratitude': 'Подтверждение благодарности',
        'suggestion': 'Подтверждение предложения',
        'bug_report': 'Подтверждение сообщения об ошибке'
    }
    
    card = f"<b>{title_map.get(feedback_type, 'Подтверждение')}</b>\n"
    if feedback_type == 'gratitude':
        card += f"\n<b>Кому:</b> {data.get('routenumber', '-')}"
    card += (
        f"\n<b>Текст:</b> {data.get('description','-')}"
        f"\n<b>ФИО:</b> {data.get('fio','-')}"
        f"\n<b>Телефон:</b> {data.get('phone','-')}"
    )
    
    await message.answer("Пожалуйста, подождите...", reply_markup=ReplyKeyboardRemove())

    if data.get('mediafileids'):
        media = [InputMediaPhoto(media=pid) for pid in data['mediafileids']]
        await message.answer_media_group(media)

    await message.answer(card, parse_mode="HTML", reply_markup=confirm_complaint_keyboard())
    await state.set_state(FeedbackStates.confirm)

@router.callback_query(F.data == "submit_complaint", FeedbackStates.confirm)
async def submit_feedback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    feedback_type = data['feedback_type']

    # Dynamic subcategory name based on type
    subcategory_name_map = {
        'gratitude': 'Общая благодарность',
        'suggestion': 'Предложение по улучшению',
        'bug_report': 'Сообщить об ошибке'
    }
    cat_key = 'feedback' if feedback_type != 'gratitude' else 'gratitude'
    # For feedback types, subcategory_id will be 1 for suggestion, 2 for bug_report
    subcat_id = 1 if feedback_type == 'suggestion' else (2 if feedback_type == 'bug_report' else 1)
    subcat_name = subcategory_name_map[feedback_type]

    dto = ComplaintDTO(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        categorykey=cat_key,
        subcategoryid=subcat_id,
        subcategoryname=subcat_name,
        address=None,
        routenumber=data.get('routenumber'), # Used for recipient in gratitude
        description=data.get('description', ''),
        fio=data.get('fio', ''),
        phone=data.get('phone', ''),
        mediafileids=data.get('mediafileids', [])
    )
    await save_complaint(dto)
    
    try:
        await callback.message.delete()
    except: pass

    await callback.message.answer("Ваше обращение принято! Спасибо.", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    admin_info = await get_admin_details(callback.from_user.id)
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard(admin_info.get('role') if admin_info else None))
    await callback.answer()
