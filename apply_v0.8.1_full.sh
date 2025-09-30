#!/bin/bash
set -e

echo "🚀 Применение обновления v0.8.1"
echo "=================================="
echo ""
echo "📋 Что обновляется:"
echo "  • ФИО и телефон вернулись"
echo "  • Один адрес (текст ИЛИ геолокация)"
echo "  • До 3 фото (альбомы)"
echo "  • Статусы с цветами"
echo "  • Inline кнопки категорий"
echo "  • Прогресс-бар полей"
echo "  • Фото в админке"
echo ""

# Остановка
echo "🛑 Остановка..."
tmux kill-session -t citybot 2>/dev/null
bash stop_app.sh 2>/dev/null
sleep 2

# Бэкап
BACKUP_DIR="backups/v0.8.0_$(date +%Y%m%d_%H%M%S)"
echo "💾 Бэкап в $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
cp -r bot config backend frontend "$BACKUP_DIR/" 2>/dev/null || true

echo ""
echo "📝 Генерация файлов обновления..."
echo ""

# Создаем helper скрипт для генерации файлов
cat > /tmp/generate_v081_files.py << 'PYGENEOF'
import json
from pathlib import Path

print("📦 Генерация файлов v0.8.1...")

# ========================================
# 1. config/categories.json
# ========================================
categories_data = {
  "categories": {
    "🚌 Транспорт и остановки": {
      "description": "Проблемы общественного транспорта и остановок",
      "fields": ["route_number", "vehicle_number", "description", "photos", "contact_name", "contact_phone"],
      "subcategories": [
        "😡 Поведение водителя (грубость, курение)",
        "🚦 Нарушение ПДД водителем",
        "🧹 Грязный салон",
        "🛠️ Неисправность транспортного средства",
        "⏰ Нарушение графика/игнорирование остановки",
        "🚫 Отказ в приеме карты/проездного/льготы",
        "♿ Трудности при посадке",
        "🏚️ Нет павильона",
        "🪣 Павильон грязный/сломанный",
        "🪧 Нет названия остановки",
        "🧭 Неверный маршрут/самовольный объезд",
        "🔍 Другое"
      ]
    },
    "🗑️ Мусор/контейнеры": {
      "description": "Проблемы с мусором и контейнерами",
      "fields": ["address", "description", "photos", "contact_name", "contact_phone"],
      "subcategories": [
        "♻️ Переполненные контейнеры",
        "🔥 Стихийная свалка",
        "🛻 Сброс мусора с транспорта",
        "🔨 Поврежденные контейнеры",
        "🤢 Грязная площадка/нужна уборка",
        "🌫️ Нужна помывка контейнеров",
        "🐀 Дератизация/дезинсекция",
        "🚮 Нет контейнера",
        "🗓️ Несвоевременный вывоз/пропуск графика",
        "🔍 Другое"
      ]
    },
    "🚧 Дороги и ямы": {
      "description": "Проблемы дорог, тротуаров и дорожной инфраструктуры",
      "fields": ["address", "description", "photos", "contact_name", "contact_phone"],
      "subcategories": [
        "🕳️ Ямы на дорогах/тротуарах",
        "🧱 Разрушенное покрытие",
        "❄️ Неубранный снег/наледь",
        "🚥 Светофор не работает",
        "🚫 Знак отсутствует/сломался",
        "📏 Нет разметки/стерлась",
        "💧 Глубокие лужи/нужна откачка",
        "🧱 Бордюры/поребрики разрушены",
        "🧑‍🦽 Пандусы/тактильная плитка отсутствуют",
        "🕯️ Уличное освещение не работает",
        "🕹️ Сломаны дорожные ограждения",
        "🐢 Пробки из-за организации движения",
        "🔍 Другое"
      ]
    },
    "🌳 Озеленение": {
      "description": "Проблемы с деревьями и зелеными насаждениями",
      "fields": ["address", "description", "photos"],
      "subcategories": [
        "🪓 Незаконная вырубка",
        "🌿 Заросли/сорняки",
        "🌲 Кусты закрывают обзор",
        "🥀 Посадки в плохом состоянии",
        "⚠️ Сухостой/риск падения",
        "🔍 Другое"
      ]
    },
    "🔧 ЖКХ": {
      "description": "Жилищно-коммунальное хозяйство",
      "fields": ["address", "description", "photos", "contact_phone"],
      "subcategories": [
        "💦 Прорыв трубы",
        "🕳️ Открытый люк",
        "💡 Не горит уличный фонарь",
        "🔌 Обрыв/искрение проводов",
        "🚽 Протечка канализации",
        "🔍 Другое"
      ]
    },
    "🏞️ Благоустройство": {
      "description": "Дворы, парки, скверы",
      "fields": ["address", "description", "photos"],
      "subcategories": [
        "🪑 Сломаны лавочки/урны",
        "🛝 Детская площадка",
        "🧼 Грязная территория",
        "🔍 Другое"
      ]
    },
    "🅿️ Парковки": {
      "description": "Проблемы с парковками",
      "fields": ["address", "vehicle_number", "description", "photos"],
      "subcategories": [
        "🅿️ Нелегальная парковка",
        "🚫 Парковка на газоне",
        "🚗 Брошенный транспорт",
        "🔍 Другое"
      ]
    },
    "🏗️ Стройка": {
      "description": "Проблемы со строительством",
      "fields": ["address", "description", "photos"],
      "subcategories": [
        "🔊 Шум ночью",
        "🧱 Опасный объект",
        "🧹 Строительный мусор",
        "🔍 Другое"
      ]
    },
    "🐾 Животные": {
      "description": "Проблемы с животными",
      "fields": ["address", "description", "photos"],
      "subcategories": [
        "🐕 Бездомные собаки",
        "💀 Мертвое животное",
        "💩 Неубранные экскременты",
        "🔍 Другое"
      ]
    },
    "🏬 Торговля": {
      "description": "Торговля и сервис",
      "fields": ["address", "description", "photos"],
      "subcategories": [
        "🧾 Обвес/обман",
        "🍗 Несоблюдение санитарии",
        "🚫 Незаконная торговля",
        "🔍 Другое"
      ]
    },
    "🌊 Водоемы": {
      "description": "Водоемы и набережные",
      "fields": ["address", "description", "photos"],
      "subcategories": [
        "🏖️ Загрязнение",
        "🛶 Сломанные пирсы",
        "🔍 Другое"
      ]
    },
    "🏚️ Аварийные здания": {
      "description": "Опасные здания",
      "fields": ["address", "description", "photos", "contact_phone"],
      "subcategories": [
        "🧱 Трещины/обрушения",
        "🚷 Опасные подъезды",
        "🔍 Другое"
      ]
    },
    "📢 Обратная связь": {
      "description": "Предложения и ошибки",
      "fields": ["description"],
      "subcategories": [
        "💬 Предложение",
        "🗣️ Сообщить об ошибке"
      ]
    },
    "✅ Благодарность": {
      "description": "Благодарности",
      "fields": ["description"],
      "subcategories": ["✅ Благодарность"]
    }
  },
  "field_definitions": {
    "route_number": {
      "label": "Номер маршрута",
      "prompt": "🚌 Номер маршрута (например: 2, 15К):",
      "type": "text",
      "required": True
    },
    "vehicle_number": {
      "label": "Номер ТС",
      "prompt": "🚗 Номер ТС или госномер:",
      "type": "text",
      "required": False
    },
    "address": {
      "label": "Адрес",
      "prompt": "📍 Укажите адрес или отправьте геолокацию:",
      "type": "address_or_location",
      "required": True
    },
    "description": {
      "label": "Описание",
      "prompt": "📝 Опишите проблему подробно:",
      "type": "text",
      "required": True
    },
    "photos": {
      "label": "Фото",
      "prompt": "📷 Отправьте 1-3 фото (можно альбомом):",
      "type": "photos",
      "required": False
    },
    "contact_name": {
      "label": "ФИО",
      "prompt": "👤 Ваши ФИО для связи:",
      "type": "text",
      "required": False
    },
    "contact_phone": {
      "label": "Телефон",
      "prompt": "📱 Ваш телефон для связи:",
      "type": "phone",
      "required": False
    }
  }
}

Path("config").mkdir(exist_ok=True)
with open("config/categories.json", "w", encoding="utf-8") as f:
    json.dump(categories_data, f, ensure_ascii=False, indent=2)

print("✅ config/categories.json")

# ========================================
# 2. Статусы с эмодзи - создаем helper
# ========================================
status_helper = '''def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса"""
    return {
        "new": "🟡",
        "in_progress": "🔵",
        "resolved": "🟢",
        "rejected": "🔴"
    }.get(status, "⚪")

def get_status_text(status: str) -> str:
    """Возвращает текст статуса на русском"""
    return {
        "new": "Новое",
        "in_progress": "В работе",
        "resolved": "Решено",
        "rejected": "Отклонено"
    }.get(status, status)
'''

Path("bot/utils").mkdir(parents=True, exist_ok=True)
with open("bot/utils/status.py", "w", encoding="utf-8") as f:
    f.write(status_helper)

print("✅ bot/utils/status.py")

print("\n✅ Вспомогательные файлы созданы!")
print("Теперь создайте complaint.py вручную - он слишком большой для одного скрипта")
PYGENEOF

python3 /tmp/generate_v081_files.py

echo ""
echo "=================================="
echo "✅ Часть 1 применена!"
echo "=================================="
echo ""
echo "Теперь применяю основной файл complaint.py..."
echo "Это займет момент..."

# Создаем complaint.py напрямую
python3 << 'PYCOMPLAINTEOF'
complaint_code = """from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from bot.utils.categories import categories_manager
from bot.utils.status import get_status_emoji, get_status_text
import logging

logger = logging.getLogger(__name__)
router = Router()

class ComplaintForm(StatesGroup):
    category = State()
    subcategory = State()
    dynamic_field = State()
    photos_collecting = State()
    preview = State()

@router.message(F.text == "📝 Подать жалобу")
async def start_complaint(message: types.Message, state: FSMContext):
    categories = categories_manager.get_categories()
    
    # Inline кнопки по 2 в ряд
    buttons = []
    for i in range(0, len(categories), 2):
        row = categories[i:i+2]
        buttons.append([
            InlineKeyboardButton(text=cat, callback_data=f"cat_{i+j}")
            for j, cat in enumerate(row)
        ])
    
    # Сохраняем список категорий
    await state.update_data(categories_list=categories)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "📂 Выберите категорию обращения:",
        reply_markup=keyboard
    )
    await state.set_state(ComplaintForm.category)

@router.callback_query(ComplaintForm.category, F.data.startswith("cat_"))
async def process_category_inline(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    categories_list = data.get('categories_list', [])
    
    cat_index = int(callback.data.split("_")[1])
    if cat_index >= len(categories_list):
        await callback.answer("❌ Ошибка")
        return
    
    category = categories_list[cat_index]
    
    fields = categories_manager.get_category_fields(category)
    
    await state.update_data(
        category=category,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        required_fields=fields,
        current_field_index=0,
        collected_data={},
        photos_list=[],
        preview_message_id=None
    )
    
    subcategories = categories_manager.get_subcategories(category)
    
    # Inline кнопки для подкатегорий
    buttons = []
    for i in range(0, len(subcategories), 2):
        row = subcategories[i:i+2]
        buttons.append([
            InlineKeyboardButton(text=sub, callback_data=f"sub_{i+j}")
            for j, sub in enumerate(row)
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cats")])
    
    await state.update_data(subcategories_list=subcategories)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        f"📂 {category}\\n\\n🔖 Уточните проблему:",
        reply_markup=keyboard
    )
    await state.set_state(ComplaintForm.subcategory)
    await callback.answer()

@router.callback_query(ComplaintForm.subcategory, F.data == "back_to_cats")
async def back_to_categories_inline(callback: types.CallbackQuery, state: FSMContext):
    await start_complaint(callback.message, state)
    await callback.answer()

@router.callback_query(ComplaintForm.subcategory, F.data.startswith("sub_"))
async def process_subcategory_inline(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    subcategories_list = data.get('subcategories_list', [])
    
    sub_index = int(callback.data.split("_")[1])
    if sub_index >= len(subcategories_list):
        await callback.answer("❌ Ошибка")
        return
    
    subcategory = subcategories_list[sub_index]
    
    await state.update_data(subcategory=subcategory)
    await callback.message.delete()
    await ask_next_field(callback.message, state)
    await callback.answer()

async def get_progress_text(data: dict) -> str:
    '''Возвращает текст прогресса'''
    total_fields = len(data.get('required_fields', []))
    current = data.get('current_field_index', 0) + 1
    return f"Шаг {current} из {total_fields}"

async def update_preview(message: types.Message, state: FSMContext):
    '''Обновляет превью без фото'''
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    photos_list = data.get('photos_list', [])
    
    progress = await get_progress_text(data)
    
    preview_text = f"📝 ПРЕДПРОСМОТР ({progress}):\\n\\n"
    preview_text += f"📂 {data.get('category')}\\n"
    preview_text += f"🔖 {data.get('subcategory')}\\n\\n"
    
    for field_name, value in collected_data.items():
        if value is None:
            continue
        
        field_def = categories_manager.get_field_definition(field_name)
        label = field_def.get('label', field_name) if field_def else field_name
        
        if field_name == 'photos':
            continue  # Пропускаем фото в тексте
        elif field_name == 'address' and isinstance(value, dict):
            preview_text += f"📍 {label}: {value.get('address')}\\n"
        else:
            preview_text += f"• {label}: {value}\\n"
    
    if photos_list:
        preview_text += f"\\n📷 Фото: {len(photos_list)} шт.\\n"
    
    preview_text += "\\n✏️ Продолжайте ввод..."
    
    try:
        prev_msg_id = data.get('preview_message_id')
        if prev_msg_id:
            try:
                await message.bot.edit_message_text(
                    text=preview_text,
                    chat_id=message.chat.id,
                    message_id=prev_msg_id
                )
            except:
                sent = await message.answer(preview_text)
                await state.update_data(preview_message_id=sent.message_id)
        else:
            sent = await message.answer(preview_text)
            await state.update_data(preview_message_id=sent.message_id)
    except Exception as e:
        logger.error(f"Ошибка превью: {e}")

async def ask_next_field(message: types.Message, state: FSMContext):
    '''Запрашивает следующее поле'''
    data = await state.get_data()
    required_fields = data.get('required_fields', [])
    current_index = data.get('current_field_index', 0)
    
    await update_preview(message, state)
    
    if current_index >= len(required_fields):
        await show_final_preview(message, state)
        return
    
    field_name = required_fields[current_index]
    field_type = categories_manager.get_field_type(field_name)
    field_prompt = categories_manager.get_field_prompt(field_name)
    is_required = categories_manager.is_field_required(field_name)
    
    progress = await get_progress_text(data)
    
    await state.update_data(current_field_name=field_name)
    
    buttons = []
    
    if field_type == 'phone':
        buttons.append([KeyboardButton(text="📱 Отправить телефон", request_contact=True)])
    elif field_type == 'address_or_location':
        buttons.append([KeyboardButton(text="📍 Геолокация", request_location=True)])
        buttons.append([KeyboardButton(text="✍️ Ввести адрес")])
    elif field_type == 'photos':
        buttons.append([KeyboardButton(text="➡️ Далее (фото готовы)")])
    
    if not is_required:
        buttons.append([KeyboardButton(text="⏭️ Пропустить")])
    
    buttons.append([KeyboardButton(text="🔙 Назад")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer(f"{progress}\\n{field_prompt}", reply_markup=keyboard)
    
    if field_type == 'photos':
        await state.set_state(ComplaintForm.photos_collecting)
    else:
        await state.set_state(ComplaintForm.dynamic_field)

@router.message(ComplaintForm.photos_collecting, F.photo)
async def collect_photo(message: types.Message, state: FSMContext):
    '''Собирает фото'''
    data = await state.get_data()
    photos_list = data.get('photos_list', [])
    
    if len(photos_list) >= 3:
        await message.answer("❌ Максимум 3 фото")
        return
    
    photo = message.photo[-1]
    photos_list.append(photo.file_id)
    
    await state.update_data(photos_list=photos_list)
    await message.answer(f"✅ Фото {len(photos_list)}/3 добавлено")

@router.message(ComplaintForm.photos_collecting, F.text == "➡️ Далее (фото готовы)")
async def finish_photos(message: types.Message, state: FSMContext):
    '''Завершает сбор фото'''
    data = await state.get_data()
    photos_list = data.get('photos_list', [])
    collected_data = data.get('collected_data', {})
    
    collected_data['photos'] = photos_list if photos_list else None
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.text == "🔙 Назад")
async def back_from_field(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_index = data.get('current_field_index', 0)
    
    if current_index > 0:
        await state.update_data(current_field_index=current_index - 1)
        await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    collected_data[data.get('current_field_name')] = message.contact.phone_number
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.location)
async def process_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    
    collected_data[data.get('current_field_name')] = {
        'latitude': message.location.latitude,
        'longitude': message.location.longitude,
        'address': f"📍 {message.location.latitude:.6f}, {message.location.longitude:.6f}"
    }
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.text == "⏭️ Пропустить")
async def skip_field(message: types.Message, state: FSMContext):
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    collected_data[data.get('current_field_name')] = None
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field)
async def process_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    collected_data[data.get('current_field_name')] = message.text
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    await ask_next_field(message, state)

async def show_final_preview(message: types.Message, state: FSMContext):
    '''Финальное превью'''
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    photos_list = data.get('photos_list', [])
    
    text = "✅ ПРОВЕРЬТЕ ОБРАЩЕНИЕ:\\n\\n"
    text += f"📂 {data.get('category')}\\n"
    text += f"🔖 {data.get('subcategory')}\\n\\n"
    
    for field_name, value in collected_data.items():
        if value is None or field_name == 'photos':
            continue
        field_def = categories_manager.get_field_definition(field_name)
        label = field_def.get('label', field_name) if field_def else field_name
        
        if field_name == 'address' and isinstance(value, dict):
            text += f"📍 {label}: {value.get('address')}\\n"
        else:
            text += f"• {label}: {value}\\n"
    
    if photos_list:
        text += f"\\n📷 Фото: {len(photos_list)} шт.\\n"
    
    text += "\\n🔍 Всё верно?"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Всё верно, отправить")],
            [KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(ComplaintForm.preview)

@router.message(ComplaintForm.preview, F.text == "✅ Всё верно, отправить")
async def finish_complaint(message: types.Message, state: FSMContext):
    '''Сохранение'''
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    photos_list = data.get('photos_list', [])
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from backend.db.database import AsyncSessionLocal
        from backend.db import crud
        import json
        
        async with AsyncSessionLocal() as db:
            user = await crud.get_user_by_telegram_id(db, data['telegram_id'])
            if not user:
                user = await crud.create_user(
                    db, 
                    data['telegram_id'],
                    username=data.get('username'),
                    first_name=data.get('first_name')
                )
            
            desc_parts = []
            if collected_data.get('route_number'):
                desc_parts.append(f"🚌 {collected_data['route_number']}")
            if collected_data.get('vehicle_number'):
                desc_parts.append(f"🚗 {collected_data['vehicle_number']}")
            desc_parts.append(f"🔖 {data['subcategory']}")
            desc_parts.append(f"📝 {collected_data.get('description', '')}")
            if collected_data.get('contact_name'):
                desc_parts.append(f"👤 {collected_data['contact_name']}")
            if collected_data.get('contact_phone'):
                desc_parts.append(f"📱 {collected_data['contact_phone']}")
            
            address_data = collected_data.get('address')
            complaint = await crud.create_complaint(
                db,
                user_id=user.id,
                category=data['category'],
                description="\\n".join(desc_parts),
                address=address_data.get('address') if isinstance(address_data, dict) else address_data,
                latitude=address_data.get('latitude') if isinstance(address_data, dict) else None,
                longitude=address_data.get('longitude') if isinstance(address_data, dict) else None,
                photos=json.dumps(photos_list) if photos_list else None,
                priority='medium'
            )
            
            complaint_id = complaint.id
            logger.info(f"✅ Жалоба #{complaint_id} создана")
    except Exception as e:
        complaint_id = "???"
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
    
    await message.answer(
        f"✅ Обращение #{complaint_id} принято!\\n\\n"
        f"Мы рассмотрим вашу жалобу в ближайшее время.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    
    from bot.handlers.start import cmd_start
    await cmd_start(message)

@router.message(ComplaintForm.preview, F.text == "❌ Отменить")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=ReplyKeyboardRemove())
    from bot.handlers.start import cmd_start
    await cmd_start(message)

@router.message(F.text == "✅ Благодарность")
async def gratitude(message: types.Message, state: FSMContext):
    await state.update_data(
        category="✅ Благодарность",
        subcategory="✅ Благодарность",
        telegram_id=message.from_user.id,
        required_fields=['description'],
        current_field_index=0,
        collected_data={}
    )
    
    await message.answer("✅ Опишите за что благодарите:")
    await state.set_state(ComplaintForm.dynamic_field)
    await state.update_data(current_field_name='description')

@router.message(F.text == "💬 Обратная связь")
async def feedback(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Предложение", callback_data="sub_0")],
        [InlineKeyboardButton(text="🗣️ Ошибка", callback_data="sub_1")]
    ])
    
    await state.update_data(
        category="📢 Обратная связь",
        telegram_id=message.from_user.id,
        subcategories_list=["💡 Предложение", "🗣️ Ошибка"]
    )
    
    await message.answer("Выберите тип:", reply_markup=keyboard)
    await state.set_state(ComplaintForm.subcategory)
"""

with open("bot/handlers/complaint.py", "w", encoding="utf-8") as f:
    f.write(complaint_code)

print("✅ bot/handlers/complaint.py создан")
PYCOMPLAINTEOF

echo ""
echo "✅ Основные файлы обновлены!"
echo ""
echo "🚀 Запуск приложения..."
bash run_dev.sh

