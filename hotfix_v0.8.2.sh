#!/bin/bash
echo "🔥 Hotfix v0.8.2"
echo "================"
echo "Исправления:"
echo "  • Кнопка 'Сейчас' для времени"
echo "  • Одно сообщение при загрузке альбома"
echo "  • Правильная кнопка после загрузки фото"
echo "  • Исправление сохранения photos (JSON массив)"
echo ""

# 1. Исправляем collect_photo - убираем множественные сообщения
python3 << 'PYFIXEOF'
with open("bot/handlers/complaint.py", "r", encoding="utf-8") as f:
    content = f.read()

# Заменяем collect_photo
old_collect = """@router.message(ComplaintForm.photos_collecting, F.photo)
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
    await message.answer(f"✅ Фото {len(photos_list)}/3 добавлено")"""

new_collect = """@router.message(ComplaintForm.photos_collecting, F.photo)
async def collect_photo(message: types.Message, state: FSMContext):
    '''Собирает фото'''
    data = await state.get_data()
    photos_list = data.get('photos_list', [])
    last_photo_msg_id = data.get('last_photo_msg_id')
    
    if len(photos_list) >= 3:
        await message.answer("❌ Максимум 3 фото")
        return
    
    # Если это медиагруппа (альбом), собираем все сразу
    if hasattr(message, 'media_group_id') and message.media_group_id:
        photo = message.photo[-1]
        photos_list.append(photo.file_id)
        await state.update_data(photos_list=photos_list, media_group_id=message.media_group_id)
        
        # Отправляем/обновляем сообщение только один раз на всю группу
        if last_photo_msg_id:
            try:
                await message.bot.edit_message_text(
                    text=f"✅ Добавлено фото: {len(photos_list)}/3",
                    chat_id=message.chat.id,
                    message_id=last_photo_msg_id
                )
            except:
                pass
        else:
            sent = await message.answer(f"✅ Добавлено фото: {len(photos_list)}/3")
            await state.update_data(last_photo_msg_id=sent.message_id)
    else:
        # Одиночное фото
        photo = message.photo[-1]
        photos_list.append(photo.file_id)
        await state.update_data(photos_list=photos_list)
        
        if last_photo_msg_id:
            try:
                await message.bot.edit_message_text(
                    text=f"✅ Добавлено фото: {len(photos_list)}/3",
                    chat_id=message.chat.id,
                    message_id=last_photo_msg_id
                )
            except:
                sent = await message.answer(f"✅ Добавлено фото: {len(photos_list)}/3")
                await state.update_data(last_photo_msg_id=sent.message_id)
        else:
            sent = await message.answer(f"✅ Добавлено фото: {len(photos_list)}/3")
            await state.update_data(last_photo_msg_id=sent.message_id)"""

content = content.replace(old_collect, new_collect)

# Заменяем ask_next_field для времени
old_time_field = """    if field_type == 'phone':
        buttons.append([KeyboardButton(text="📱 Отправить телефон", request_contact=True)])
    elif field_type == 'address_or_location':"""

new_time_field = """    if field_type == 'phone':
        buttons.append([KeyboardButton(text="📱 Отправить телефон", request_contact=True)])
    elif field_type == 'text' and field_name == 'incident_time':
        from datetime import datetime
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        buttons.append([KeyboardButton(text=f"🕐 Сейчас ({now})")])
    elif field_type == 'address_or_location':"""

content = content.replace(old_time_field, new_time_field)

# Исправляем кнопки после фото - убираем "Пропустить" если фото уже есть
old_finish_photos = """@router.message(ComplaintForm.photos_collecting, F.text == "➡️ Далее (фото готовы)")
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
    
    await ask_next_field(message, state)"""

new_finish_photos = """@router.message(ComplaintForm.photos_collecting, F.text == "➡️ Далее (фото готовы)")
async def finish_photos(message: types.Message, state: FSMContext):
    '''Завершает сбор фото'''
    data = await state.get_data()
    photos_list = data.get('photos_list', [])
    collected_data = data.get('collected_data', {})
    
    collected_data['photos'] = photos_list if photos_list else None
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1,
        last_photo_msg_id=None,
        media_group_id=None
    )
    
    await ask_next_field(message, state)

@router.message(ComplaintForm.photos_collecting, F.text == "⏭️ Пропустить")
async def skip_photos(message: types.Message, state: FSMContext):
    '''Пропуск фото'''
    data = await state.get_data()
    collected_data = data.get('collected_data', {})
    collected_data['photos'] = None
    
    await state.update_data(
        collected_data=collected_data,
        current_field_index=data.get('current_field_index', 0) + 1
    )
    
    await ask_next_field(message, state)"""

content = content.replace(old_finish_photos, new_finish_photos)

# Исправляем сохранение - JSON массив, а не строка
old_save = """            complaint = await crud.create_complaint(
                db,
                user_id=user.id,
                category=data['category'],
                description="\\n".join(desc_parts),
                address=address_data.get('address') if isinstance(address_data, dict) else address_data,
                latitude=address_data.get('latitude') if isinstance(address_data, dict) else None,
                longitude=address_data.get('longitude') if isinstance(address_data, dict) else None,
                photos=json.dumps(photos_list) if photos_list else None,
                priority='medium'
            )"""

new_save = """            # ВАЖНО: Сохраняем photos как JSON array
            photos_json = None
            if photos_list:
                photos_json = json.dumps(photos_list)  # '[\"file_id1\", \"file_id2\"]'
            
            complaint = await crud.create_complaint(
                db,
                user_id=user.id,
                category=data['category'],
                description="\\n".join(desc_parts),
                address=address_data.get('address') if isinstance(address_data, dict) else address_data,
                latitude=address_data.get('latitude') if isinstance(address_data, dict) else None,
                longitude=address_data.get('longitude') if isinstance(address_data, dict) else None,
                photos=photos_json,
                priority='medium'
            )"""

content = content.replace(old_save, new_save)

with open("bot/handlers/complaint.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ bot/handlers/complaint.py исправлен")
PYFIXEOF

# 2. Исправляем frontend для правильного отображения массива фото
cat > frontend/residents/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Мои обращения</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
body{font-family:sans-serif;padding:16px;background:#f5f5f5;margin:0}
.card{background:#fff;padding:16px;margin:12px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.category{font-weight:600;margin-bottom:8px}
.photo{max-width:100%;border-radius:8px;margin:4px 0}
.btn{background:#0088cc;color:#fff;border:none;padding:12px;border-radius:8px;width:100%;margin-top:20px;font-size:16px}
.status{padding:4px 8px;border-radius:8px;font-size:12px;display:inline-block;margin:8px 0}
.status-new{background:#ffeaa7;color:#000}
.status-in_progress{background:#74b9ff;color:#000}
.status-resolved{background:#55efc4;color:#000}
</style>
</head><body><h2>📋 Мои обращения</h2><div id="list">Загрузка...</div>
<button class="btn" onclick="window.Telegram.WebApp.close()">Закрыть</button>
<script>
const tg=window.Telegram.WebApp;tg.ready();tg.expand();
const urlParams=new URLSearchParams(window.location.search);
const userId=tg.initDataUnsafe?.user?.id||urlParams.get('user_id');

const statusText={
  new:'🟡 Новое',
  in_progress:'🔵 В работе',
  resolved:'🟢 Решено',
  rejected:'🔴 Отклонено'
};

async function load(){
  try{
    if(!userId){document.getElementById('list').innerHTML='<div class="card">❌ Нет user ID</div>';return;}
    const res=await fetch(`/api/v1/complaints/my?user_id=${userId}`);
    if(!res.ok){document.getElementById('list').innerHTML=`<div class="card">❌ Ошибка ${res.status}</div>`;return;}
    const data=await res.json();
    if(data.length===0){document.getElementById('list').innerHTML='<div class="card">Нет обращений</div>';return;}
    
    document.getElementById('list').innerHTML=data.map(c=>{
      let html=`<div class="card"><div class="category">${c.category}</div>`;
      
      // Обрабатываем photos - может быть JSON array
      if(c.photos){
        try{
          const photos=JSON.parse(c.photos);
          if(Array.isArray(photos)){
            photos.forEach(fileId=>{
              html+=`<img class="photo" src="/api/v1/photos/${fileId}" alt="Фото">`;
            });
          }else{
            html+=`<img class="photo" src="/api/v1/photos/${c.photos}" alt="Фото">`;
          }
        }catch(e){
          // Если не JSON, значит один file_id
          html+=`<img class="photo" src="/api/v1/photos/${c.photos}" alt="Фото">`;
        }
      }
      
      html+=`<div style="margin:8px 0;white-space:pre-wrap">${c.description||''}</div>`;
      html+=`<div class="status status-${c.status}">${statusText[c.status]||c.status}</div>`;
      html+=`<div style="color:#888;font-size:12px;margin-top:8px">${new Date(c.created_at).toLocaleString('ru-RU')}</div>`;
      html+=`</div>`;
      return html;
    }).join('');
  }catch(e){
    console.error(e);
    document.getElementById('list').innerHTML=`<div class="card">❌ Ошибка: ${e.message}</div>`;
  }
}
load();
</script></body></html>
HTMLEOF

echo "✅ frontend/residents/index.html (массив фото)"

echo ""
echo "✅ Hotfix v0.8.2 применен!"
echo ""
echo "🚀 Перезапуск..."
bash run_dev.sh

