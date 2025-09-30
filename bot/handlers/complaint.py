from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo
from bot.utils.categories import categories_manager

router = Router()

class ComplaintForm(StatesGroup):
    category = State()
    subcategory = State()
    dynamic_field = State()  # Для динамических полей

@router.message(F.text == "📝 Подать жалобу")
async def start_complaint(message: types.Message, state: FSMContext):
    categories = categories_manager.get_categories()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat)] for cat in categories],
        resize_keyboard=True
    )
    await message.answer("Выберите категорию обращения:", reply_markup=keyboard)
    await state.set_state(ComplaintForm.category)

@router.message(ComplaintForm.category)
async def process_category(message: types.Message, state: FSMContext):
    category = message.text
    categories = categories_manager.get_categories()
    
    if category not in categories:
        await message.answer("❌ Выберите категорию из предложенных")
        return
    
    # Получаем поля для этой категории
    fields = categories_manager.get_category_fields(category)
    
    await state.update_data(
        category=category,
        telegram_id=message.from_user.id,
        required_fields=fields,
        current_field_index=0,
        collected_data={}
    )
    
    subcategories = categories_manager.get_subcategories(category)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=sub)] for sub in subcategories],
        resize_keyboard=True
    )
    
    await message.answer("Уточните проблему:", reply_markup=keyboard)
    await state.set_state(ComplaintForm.subcategory)

@router.message(ComplaintForm.subcategory)
async def process_subcategory(message: types.Message, state: FSMContext):
    await state.update_data(subcategory=message.text)
    
    # Начинаем сбор полей
    await ask_next_field(message, state)

async def ask_next_field(message: types.Message, state: FSMContext):
    """Запрашивает следующее поле из списка"""
    data = await state.get_data()
    required_fields = data.get('required_fields', [])
    current_index = data.get('current_field_index', 0)
    
    if current_index >= len(required_fields):
        # Все поля собраны - завершаем
        await finish_complaint(message, state)
        return
    
    # Получаем текущее поле
    field_name = required_fields[current_index]
    field_type = categories_manager.get_field_type(field_name)
    field_prompt = categories_manager.get_field_prompt(field_name)
    is_required = categories_manager.is_field_required(field_name)
    
    await state.update_data(current_field_name=field_name)
    
    # Формируем клавиатуру в зависимости от типа поля
    if field_type == 'address_or_location':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
                [KeyboardButton(text="✍️ Ввести адрес вручную")],
                [KeyboardButton(text="⏭️ Пропустить")] if not is_required else []
            ],
            resize_keyboard=True
        )
    elif field_type == 'location':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
                [KeyboardButton(text="⏭️ Пропустить")] if not is_required else []
            ],
            resize_keyboard=True
        )
    else:
        # Обычное текстовое поле
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏭️ Пропустить")] if not is_required else []
            ],
            resize_keyboard=True
        ) if not is_required else ReplyKeyboardRemove()
    
    await message.answer(field_prompt, reply_markup=keyboard)
    await state.set_state(ComplaintForm.dynamic_field)

@router.message(ComplaintForm.dynamic_field, F.location)
async def process_location_field(message: types.Message, state: FSMContext):
    """Обработка геолокации"""
    data = await state.get_data()
    field_name = data.get('current_field_name')
    collected_data = data.get('collected_data', {})
    
    collected_data[field_name] = {
        'type': 'location',
        'latitude': message.location.latitude,
        'longitude': message.location.longitude,
        'address': f"📍 {message.location.latitude:.6f}, {message.location.longitude:.6f}"
    }
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.text == "✍️ Ввести адрес вручную")
async def ask_address_manual(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите адрес:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(ComplaintForm.dynamic_field, F.text == "⏭️ Пропустить")
async def skip_field(message: types.Message, state: FSMContext):
    """Пропуск необязательного поля"""
    data = await state.get_data()
    field_name = data.get('current_field_name')
    collected_data = data.get('collected_data', {})
    
    collected_data[field_name] = None
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field)
async def process_text_field(message: types.Message, state: FSMContext):
    """Обработка текстового поля"""
    data = await state.get_data()
    field_name = data.get('current_field_name')
    collected_data = data.get('collected_data', {})
    
    collected_data[field_name] = message.text
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)

async def finish_complaint(message: types.Message, state: FSMContext):
    """Завершение создания жалобы"""
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    
    # Формируем данные для сохранения
    complaint_data = {
        'telegram_id': data['telegram_id'],
        'category': data['category'],
        'subcategory': data.get('subcategory', ''),
        'description': collected_data.get('description', ''),
        'route_number': collected_data.get('route_number'),
        'vehicle_number': collected_data.get('vehicle_number'),
        'address': None,
        'latitude': None,
        'longitude': None
    }
    
    # Обрабатываем адрес/локацию
    if 'address' in collected_data:
        if isinstance(collected_data['address'], dict):
            complaint_data['latitude'] = collected_data['address'].get('latitude')
            complaint_data['longitude'] = collected_data['address'].get('longitude')
            complaint_data['address'] = collected_data['address'].get('address')
        else:
            complaint_data['address'] = collected_data['address']
    
    if 'location' in collected_data and collected_data['location']:
        if isinstance(collected_data['location'], dict):
            complaint_data['latitude'] = collected_data['location'].get('latitude')
            complaint_data['longitude'] = collected_data['location'].get('longitude')
            if not complaint_data['address']:
                complaint_data['address'] = collected_data['location'].get('address')
    
    # Сохраняем в базу данных
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from backend.db.database import AsyncSessionLocal
        from backend.db import crud
        
        async with AsyncSessionLocal() as db:
            # Создаем или получаем пользователя
            user = await crud.get_user_by_telegram_id(db, complaint_data['telegram_id'])
            if not user:
                user = await crud.create_user(
                    db, 
                    complaint_data['telegram_id'],
                    username=message.from_user.username,
                    first_name=message.from_user.first_name
                )
            
            # Формируем полное описание
            full_description = f"{complaint_data['subcategory']}\n{complaint_data['description']}"
            if complaint_data.get('route_number'):
                full_description = f"Маршрут: {complaint_data['route_number']}\n{full_description}"
            if complaint_data.get('vehicle_number'):
                full_description = f"ТС: {complaint_data['vehicle_number']}\n{full_description}"
            
            # Создаем жалобу
            complaint = await crud.create_complaint(
                db,
                user_id=user.id,
                category=complaint_data['category'],
                description=full_description,
                address=complaint_data.get('address'),
                latitude=complaint_data.get('latitude'),
                longitude=complaint_data.get('longitude'),
                priority='medium'
            )
            
            complaint_id = complaint.id
    except Exception as e:
        complaint_id = "???"
        print(f"Ошибка сохранения жалобы: {e}")
        import traceback
        traceback.print_exc()
    
    # Формируем сообщение о принятии жалобы
    text_parts = [f"✅ Обращение #{complaint_id} принято!\n"]
    text_parts.append(f"📂 Категория: {complaint_data['category']}")
    text_parts.append(f"🔖 Тип: {complaint_data['subcategory']}")
    
    if complaint_data.get('route_number'):
        text_parts.append(f"🚌 Маршрут: {complaint_data['route_number']}")
    if complaint_data.get('vehicle_number'):
        text_parts.append(f"🚗 ТС: {complaint_data['vehicle_number']}")
    if complaint_data.get('description'):
        text_parts.append(f"📝 Описание: {complaint_data['description']}")
    if complaint_data.get('address'):
        text_parts.append(f"📍 Адрес: {complaint_data['address']}")
    
    text_parts.append("\nМы рассмотрим вашу жалобу в ближайшее время.")
    text_parts.append("Отслеживайте статус в разделе 📋 Мои обращения")
    
    text = "\n".join(text_parts)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Подать жалобу")],
            [KeyboardButton(
                text="📋 Мои обращения",
                web_app=WebAppInfo(url="https://sterx.mooo.com:8443/webapp/residents")
            )],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()

@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: types.Message):
    categories = categories_manager.get_categories()
    categories_text = "\n".join([f"• {cat}" for cat in categories[:5]])
    
    await message.answer(
        f"ℹ️ Как использовать бот:\n\n"
        f"📝 Подать жалобу - создать новое обращение\n"
        f"📋 Мои обращения - посмотреть историю в Mini App\n"
        f"ℹ️ Помощь - это сообщение\n\n"
        f"📂 Доступные категории:\n{categories_text}\n...и другие\n\n"
        f"Выберите категорию и следуйте инструкциям бота."
    )
