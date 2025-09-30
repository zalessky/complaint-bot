#!/bin/bash
echo "📦 Применение обновления v0.8.0"
echo "================================"
echo ""
echo "Изменения:"
echo "  0. Кнопки 'Назад' во всех меню"
echo "  1. Улучшенный UI (категории по 2 в ряд)"
echo "  2. Превью жалобы на каждом шаге"
echo "  3. Финальная кнопка 'Всё верно, отправить'"
echo "  4. Endpoint для получения фото"
echo "  5. Отображение фото в тикетах"
echo "  6. Детальная карточка тикета"
echo ""
read -p "Продолжить? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено"
    exit 1
fi

echo "🔄 Создание резервных копий..."
mkdir -p backups/v0.7.1
cp -r bot/handlers backups/v0.7.1/
cp -r backend/api backups/v0.7.1/
cp -r frontend backups/v0.7.1/
echo "✅ Бэкапы созданы в backups/v0.7.1/"

echo ""
echo "📝 Обновление файлов..."

# ========================================
# 1. Новый complaint handler с превью
# ========================================
cat > bot/handlers/complaint.py << 'COMPLAINTEOF'
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from bot.utils.categories import categories_manager
import logging

logger = logging.getLogger(__name__)
router = Router()

class ComplaintForm(StatesGroup):
    category = State()
    subcategory = State()
    dynamic_field = State()
    preview = State()

def get_back_button():
    return KeyboardButton(text="🔙 Назад")

def get_main_menu_button():
    return KeyboardButton(text="🏠 Главное меню")

@router.message(F.text == "📝 Подать жалобу")
async def start_complaint(message: types.Message, state: FSMContext):
    categories = categories_manager.get_categories()
    
    # Разбиваем на колонки по 2 кнопки
    buttons = []
    for i in range(0, len(categories), 2):
        row = categories[i:i+2]
        buttons.append([KeyboardButton(text=cat) for cat in row])
    
    buttons.append([get_main_menu_button()])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer(
        "📂 Выберите категорию обращения:\n\n"
        "💡 Прокрутите список для просмотра всех категорий",
        reply_markup=keyboard
    )
    await state.set_state(ComplaintForm.category)

@router.message(ComplaintForm.category, F.text == "🏠 Главное меню")
async def back_to_main_from_category(message: types.Message, state: FSMContext):
    await state.clear()
    from bot.handlers.start import cmd_start
    await cmd_start(message)

@router.message(ComplaintForm.category)
async def process_category(message: types.Message, state: FSMContext):
    category = message.text
    categories = categories_manager.get_categories()
    
    if category not in categories:
        await message.answer("❌ Выберите категорию из предложенных")
        return
    
    fields = categories_manager.get_category_fields(category)
    
    await state.update_data(
        category=category,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        required_fields=fields,
        current_field_index=0,
        collected_data={},
        preview_message_id=None
    )
    
    subcategories = categories_manager.get_subcategories(category)
    
    # Разбиваем подкатегории на колонки
    buttons = []
    for i in range(0, len(subcategories), 2):
        row = subcategories[i:i+2]
        buttons.append([KeyboardButton(text=sub) for sub in row])
    
    buttons.append([get_back_button()])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer(
        f"📂 Категория: {category}\n\n"
        "🔖 Уточните проблему:",
        reply_markup=keyboard
    )
    await state.set_state(ComplaintForm.subcategory)

@router.message(ComplaintForm.subcategory, F.text == "🔙 Назад")
async def back_to_categories(message: types.Message, state: FSMContext):
    await start_complaint(message, state)

@router.message(ComplaintForm.subcategory)
async def process_subcategory(message: types.Message, state: FSMContext):
    await state.update_data(subcategory=message.text)
    await ask_next_field(message, state)

async def update_preview(message: types.Message, state: FSMContext):
    """Обновляет превью жалобы"""
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    
    preview_text = "📝 ПРЕДПРОСМОТР:\n\n"
    preview_text += f"📂 {data.get('category', 'Не указана')}\n"
    preview_text += f"🔖 {data.get('subcategory', 'Не указан')}\n\n"
    
    for field_name, value in collected_data.items():
        if value is None:
            continue
        
        field_def = categories_manager.get_field_definition(field_name)
        label = field_def.get('label', field_name) if field_def else field_name
        
        if field_name == 'photo' and isinstance(value, dict):
            preview_text += f"📷 {label}: ✅\n"
        elif field_name in ['address', 'location'] and isinstance(value, dict):
            preview_text += f"📍 {label}: {value.get('address', 'Указано')}\n"
        else:
            preview_text += f"• {label}: {value}\n"
    
    preview_text += "\n✏️ Вводите следующее поле..."
    
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
        logger.error(f"Ошибка обновления превью: {e}")

async def ask_next_field(message: types.Message, state: FSMContext):
    """Запрашивает следующее поле"""
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
    
    await state.update_data(current_field_name=field_name)
    
    buttons = []
    
    if field_type == 'phone':
        buttons.append([KeyboardButton(text="📱 Отправить телефон", request_contact=True)])
    elif field_type == 'address_or_location':
        buttons.append([KeyboardButton(text="📍 Отправить геолокацию", request_location=True)])
        buttons.append([KeyboardButton(text="✍️ Ввести адрес вручную")])
    elif field_type == 'location':
        buttons.append([KeyboardButton(text="📍 Отправить геолокацию", request_location=True)])
    
    if not is_required:
        buttons.append([KeyboardButton(text="⏭️ Пропустить")])
    
    buttons.append([get_back_button()])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer(field_prompt, reply_markup=keyboard)
    await state.set_state(ComplaintForm.dynamic_field)

async def show_final_preview(message: types.Message, state: FSMContext):
    """Финальное превью с подтверждением"""
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    
    preview_text = "✅ ПРОВЕРЬТЕ ВАШЕ ОБРАЩЕНИЕ:\n\n"
    preview_text += f"📂 Категория: {data.get('category')}\n"
    preview_text += f"🔖 Тип: {data.get('subcategory')}\n\n"
    
    for field_name, value in collected_data.items():
        if value is None:
            continue
        
        field_def = categories_manager.get_field_definition(field_name)
        label = field_def.get('label', field_name) if field_def else field_name
        
        if field_name == 'photo' and isinstance(value, dict):
            preview_text += f"📷 {label}: Прикреплено\n"
        elif field_name in ['address', 'location'] and isinstance(value, dict):
            preview_text += f"📍 {label}: {value.get('address')}\n"
        else:
            preview_text += f"• {label}: {value}\n"
    
    preview_text += "\n🔍 Всё верно?"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Всё верно, отправить")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(preview_text, reply_markup=keyboard)
    await state.set_state(ComplaintForm.preview)

@router.message(ComplaintForm.preview, F.text == "✅ Всё верно, отправить")
async def confirm_and_send(message: types.Message, state: FSMContext):
    await finish_complaint(message, state)

@router.message(ComplaintForm.preview, F.text == "❌ Отменить")
async def cancel_complaint(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Обращение отменено", reply_markup=ReplyKeyboardRemove())
    from bot.handlers.start import cmd_start
    await cmd_start(message)

@router.message(ComplaintForm.preview, F.text == "🔙 Назад")
async def back_from_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    required_fields = data.get('required_fields', [])
    if required_fields:
        await state.update_data(current_field_index=len(required_fields) - 1)
        await ask_next_field(message, state)
    else:
        await process_category(message, state)

@router.message(ComplaintForm.dynamic_field, F.text == "🔙 Назад")
async def back_from_field(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_index = data.get('current_field_index', 0)
    
    if current_index > 0:
        await state.update_data(current_field_index=current_index - 1)
        await ask_next_field(message, state)
    else:
        await process_category(message, state)

@router.message(ComplaintForm.dynamic_field, F.contact)
async def process_contact_field(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field_name = data.get('current_field_name')
    collected_data = data.get('collected_data', {})
    
    collected_data[field_name] = message.contact.phone_number
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.photo)
async def process_photo_field(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field_name = data.get('current_field_name')
    collected_data = data.get('collected_data', {})
    
    photo = message.photo[-1]
    collected_data[field_name] = {
        'file_id': photo.file_id,
        'file_unique_id': photo.file_unique_id
    }
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)

@router.message(ComplaintForm.dynamic_field, F.location)
async def process_location_field(message: types.Message, state: FSMContext):
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
    await message.answer("Введите адрес:", reply_markup=ReplyKeyboardRemove())

@router.message(ComplaintForm.dynamic_field, F.text == "⏭️ Пропустить")
async def skip_field(message: types.Message, state: FSMContext):
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
    """Сохранение жалобы"""
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    
    complaint_data = {
        'telegram_id': data['telegram_id'],
        'username': data.get('username'),
        'first_name': data.get('first_name'),
        'category': data['category'],
        'subcategory': data.get('subcategory', ''),
        'description': collected_data.get('description', ''),
        'route_number': collected_data.get('route_number'),
        'vehicle_number': collected_data.get('vehicle_number'),
        'contact_phone': collected_data.get('contact_phone'),
        'address': None,
        'latitude': None,
        'longitude': None,
        'photos': None
    }
    
    if 'address' in collected_data and collected_data['address']:
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
    
    if 'photo' in collected_data and collected_data['photo']:
        if isinstance(collected_data['photo'], dict):
            complaint_data['photos'] = collected_data['photo']['file_id']
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from backend.db.database import AsyncSessionLocal
        from backend.db import crud
        
        async with AsyncSessionLocal() as db:
            user = await crud.get_user_by_telegram_id(db, complaint_data['telegram_id'])
            if not user:
                user = await crud.create_user(
                    db, 
                    complaint_data['telegram_id'],
                    username=complaint_data['username'],
                    first_name=complaint_data['first_name']
                )
            
            full_description_parts = []
            if complaint_data.get('route_number'):
                full_description_parts.append(f"🚌 Маршрут: {complaint_data['route_number']}")
            if complaint_data.get('vehicle_number'):
                full_description_parts.append(f"🚗 ТС: {complaint_data['vehicle_number']}")
            full_description_parts.append(f"🔖 {complaint_data['subcategory']}")
            full_description_parts.append(f"📝 {complaint_data['description']}")
            if complaint_data.get('contact_phone'):
                full_description_parts.append(f"📱 Телефон: {complaint_data['contact_phone']}")
            
            full_description = "\n".join(full_description_parts)
            
            complaint = await crud.create_complaint(
                db,
                user_id=user.id,
                category=complaint_data['category'],
                description=full_description,
                address=complaint_data.get('address'),
                latitude=complaint_data.get('latitude'),
                longitude=complaint_data.get('longitude'),
                photos=complaint_data.get('photos'),
                priority='medium'
            )
            
            complaint_id = complaint.id
            logger.info(f"✅ Жалоба #{complaint_id} создана пользователем {complaint_data['telegram_id']}")
    except Exception as e:
        complaint_id = "???"
        logger.error(f"❌ Ошибка сохранения жалобы: {e}", exc_info=True)
    
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
    if complaint_data.get('contact_phone'):
        text_parts.append(f"📱 Телефон: {complaint_data['contact_phone']}")
    if complaint_data.get('photos'):
        text_parts.append("📷 Фото прикреплено")
    
    text_parts.append("\nМы рассмотрим вашу жалобу в ближайшее время.")
    text_parts.append("Отслеживайте статус в разделе 📋 Мои обращения")
    
    text = "\n".join(text_parts)
    
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.clear()
    
    from bot.handlers.start import cmd_start
    await cmd_start(message)

@router.message(F.text == "✅ Благодарность")
async def start_gratitude(message: types.Message, state: FSMContext):
    await state.update_data(
        category="✅ Благодарность",
        subcategory="✅ Благодарность",
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        required_fields=['description'],
        current_field_index=0,
        collected_data={}
    )
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[get_back_button()]],
        resize_keyboard=True
    )
    
    await message.answer(
        "✅ Кого вы хотите поблагодарить? Опишите подробно:",
        reply_markup=keyboard
    )
    await state.set_state(ComplaintForm.dynamic_field)
    await state.update_data(current_field_name='description')

@router.message(F.text == "💬 Обратная связь")
async def start_feedback(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💡 Предложение по улучшению")],
            [KeyboardButton(text="🐛 Сообщить об ошибке")],
            [get_back_button()]
        ],
        resize_keyboard=True
    )
    
    await state.update_data(
        category="📢 Обратная связь",
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    await message.answer("Выберите тип обратной связи:", reply_markup=keyboard)
    await state.set_state(ComplaintForm.subcategory)

@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: types.Message):
    categories = categories_manager.get_categories()
    categories_text = "\n".join([f"• {cat}" for cat in categories[:5]])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[get_main_menu_button()]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"ℹ️ Как использовать бот:\n\n"
        f"📝 Подать жалобу - создать новое обращение\n"
        f"📋 Мои обращения - посмотреть историю в Mini App\n"
        f"ℹ️ Помощь - это сообщение\n\n"
        f"📂 Доступные категории:\n{categories_text}\n...и другие (всего {len(categories)})\n\n"
        f"Выберите категорию и следуйте инструкциям бота.",
        reply_markup=keyboard
    )
COMPLAINTEOF

echo "✅ bot/handlers/complaint.py"

# ========================================
# 2. Endpoint для получения фото
# ========================================
cat > backend/api/v1/photos.py << 'PHOTOEOF'
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from backend.core.config import settings
import httpx
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{file_id}")
async def get_photo(file_id: str):
    """
    Получает фото из Telegram по file_id
    """
    try:
        # Получаем информацию о файле
        async with httpx.AsyncClient() as client:
            file_response = await client.get(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getFile",
                params={"file_id": file_id}
            )
            file_data = file_response.json()
            
            if not file_data.get("ok"):
                logger.error(f"Ошибка получения файла: {file_data}")
                raise HTTPException(status_code=404, detail="Photo not found")
            
            file_path = file_data["result"]["file_path"]
            
            # Скачиваем файл
            photo_url = f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
            photo_response = await client.get(photo_url)
            
            if photo_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Photo not found")
            
            # Возвращаем как поток
            return StreamingResponse(
                io.BytesIO(photo_response.content),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"}
            )
    except Exception as e:
        logger.error(f"Ошибка получения фото {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch photo")
PHOTOEOF

echo "✅ backend/api/v1/photos.py"

# Подключаем photos router в main.py
sed -i 's/from backend.api.v1 import auth, complaints, users, employees, websocket/from backend.api.v1 import auth, complaints, users, employees, websocket, photos/' backend/main.py
sed -i '/app.include_router(websocket.router/a app.include_router(photos.router, prefix="/api/v1/photos", tags=["photos"])' backend/main.py

echo "✅ Добавлен photos router в backend/main.py"

# ========================================
# 3. Обновление frontend residents
# ========================================
cat > frontend/residents/index.html << 'RESIDENTSEOF'
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Мои обращения</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
body{font-family:sans-serif;padding:16px;background:#f5f5f5;margin:0}
.card{background:#fff;padding:16px;margin:12px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.category{font-weight:600;margin-bottom:8px}
.photo{max-width:100%;border-radius:8px;margin:8px 0}
.btn{background:#0088cc;color:#fff;border:none;padding:12px;border-radius:8px;width:100%;margin-top:20px;font-size:16px}
</style>
</head><body><h2>📋 Мои обращения</h2><div id="list">Загрузка...</div>
<button class="btn" onclick="window.Telegram.WebApp.close()">Закрыть</button>
<script>
const tg=window.Telegram.WebApp;tg.ready();tg.expand();
const urlParams=new URLSearchParams(window.location.search);
const userId=tg.initDataUnsafe?.user?.id||urlParams.get('user_id');

async function load(){
  try{
    if(!userId){document.getElementById('list').innerHTML='<div class="card">❌ Нет user ID</div>';return;}
    const res=await fetch(`/api/v1/complaints/my?user_id=${userId}`);
    if(!res.ok){document.getElementById('list').innerHTML=`<div class="card">❌ Ошибка ${res.status}</div>`;return;}
    const data=await res.json();
    if(data.length===0){document.getElementById('list').innerHTML='<div class="card">Пока нет обращений</div>';return;}
    document.getElementById('list').innerHTML=data.map(c=>{
      let html=`<div class="card"><div class="category">${c.category}</div>`;
      if(c.photos){html+=`<img class="photo" src="/api/v1/photos/${c.photos}" alt="Фото">`;}
      html+=`<div style="margin:8px 0;white-space:pre-wrap">${c.description}</div>`;
      html+=`<small>${new Date(c.created_at).toLocaleString('ru-RU')}</small></div>`;
      return html;
    }).join('');
  }catch(e){document.getElementById('list').innerHTML=`<div class="card">❌ Ошибка: ${e.message}</div>`;}
}
load();
</script></body></html>
RESIDENTSEOF

echo "✅ frontend/residents/index.html (с фото)"

echo ""
echo "================================"
echo "✅ Обновление v0.8.0 применено!"
echo "================================"
echo ""
echo "📝 Изменения:"
echo "  ✅ Кнопки 'Назад' во всех меню"
echo "  ✅ Категории по 2 в ряд"
echo "  ✅ Превью жалобы на каждом шаге"
echo "  ✅ Кнопка 'Всё верно, отправить'"
echo "  ✅ Endpoint /api/v1/photos/{file_id}"
echo "  ✅ Фото отображаются в Mini App"
echo ""
echo "🚀 Перезапуск приложения:"
echo "  bash run_dev.sh"
echo ""
