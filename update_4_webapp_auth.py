#!/usr/bin/env python3
"""
Обновление 4: Исправление авторизации Mini App
"""
print("📦 Обновление 4: Авторизация Mini App")
print("="*60)

# Упрощенная security для работы с Telegram Mini Apps
security_py = '''import hmac
import hashlib
import json
from urllib.parse import parse_qs, unquote
from fastapi import HTTPException, Header
from typing import Optional

def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Валидирует initData от Telegram Mini App
    """
    try:
        # Парсим данные
        parsed = parse_qs(init_data)
        
        # Извлекаем hash
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            raise ValueError("Missing hash")
        
        # Удаляем hash из данных для проверки
        data_check_arr = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                values = parsed[key]
                for value in values:
                    data_check_arr.append(f"{key}={value}")
        
        data_check_string = "\\n".join(data_check_arr)
        
        # Создаем secret key
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем hash
        if calculated_hash != received_hash:
            raise ValueError("Invalid hash")
        
        # Извлекаем данные пользователя
        user_json = parsed.get('user', [None])[0]
        if user_json:
            user = json.loads(unquote(user_json))
            return user
        
        raise ValueError("No user data")
        
    except Exception as e:
        print(f"⚠️  Ошибка валидации Telegram data: {e}")
        raise HTTPException(status_code=401, detail="Auth failed")

def get_current_user_id(init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"), bot_token: str = None) -> int:
    """
    Получает ID текущего пользователя из Telegram initData
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing auth data")
    
    if not bot_token:
        from backend.core.config import settings
        bot_token = settings.BOT_TOKEN
    
    user = validate_telegram_init_data(init_data, bot_token)
    return user.get('id')
'''

with open("backend/core/security.py", "w", encoding="utf-8") as f:
    f.write(security_py)

print("✅ Обновлен backend/core/security.py")
print("  • Правильная валидация Telegram initData")
print("  • Поддержка hash verification")

# Обновляем dependencies для использования новой security
dependencies_py = '''from fastapi import Depends, Header, HTTPException
from typing import Optional
from backend.core.config import settings
from backend.core.security import get_current_user_id

async def get_current_user(
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
) -> int:
    """
    Dependency для получения текущего пользователя
    """
    return get_current_user_id(init_data, settings.BOT_TOKEN)

async def get_current_admin(
    user_id: int = Depends(get_current_user)
) -> int:
    """
    Dependency для проверки прав администратора
    """
    if user_id not in settings.admin_ids_list and user_id != settings.SUPER_ADMIN_ID:
        raise HTTPException(status_code=403, detail="Access denied")
    return user_id
'''

with open("backend/core/dependencies.py", "w", encoding="utf-8") as f:
    f.write(dependencies_py)

print("✅ Обновлен backend/core/dependencies.py")

print("\n" + "="*60)
print("✅ Обновление 4 завершено!")
print("\n📝 Перезапустите backend:")
print("  bash stop_app.sh")
print("  bash start_app.sh")
print("\nИли в режиме отладки:")
print("  PYTHONPATH=. poetry run python backend/main.py")
