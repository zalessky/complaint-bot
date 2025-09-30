from fastapi import Depends, Header, HTTPException, Query
from typing import Optional
from backend.core.config import settings
from backend.core.security import get_current_user_id
import logging

logger = logging.getLogger(__name__)

async def get_current_user(
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    debug_user_id: Optional[int] = Query(None, alias="user_id")  # Для тестирования
) -> int:
    """
    Dependency для получения текущего пользователя
    """
    
    # Режим отладки - если передан user_id в query
    if debug_user_id and not init_data:
        logger.warning(f"⚠️  РЕЖИМ ОТЛАДКИ: используется user_id={debug_user_id}")
        return debug_user_id
    
    logger.info(f"🔍 Получен init_data: {init_data[:100] if init_data else 'None'}...")
    
    if not init_data:
        logger.error("❌ Missing init_data")
        raise HTTPException(status_code=401, detail="Missing auth data")
    
    try:
        user_id = get_current_user_id(init_data, settings.BOT_TOKEN)
        logger.info(f"✅ Авторизован пользователь: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"❌ Ошибка авторизации: {e}")
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")

async def get_admin_user(
    user_id: int = Depends(get_current_user)
) -> int:
    """
    Dependency для проверки прав администратора
    """
    if user_id not in settings.admin_ids_list and user_id != settings.SUPER_ADMIN_ID:
        raise HTTPException(status_code=403, detail="Access denied")
    return user_id

async def get_current_admin(
    user_id: int = Depends(get_current_user)
) -> int:
    """
    Dependency для проверки прав администратора
    """
    if user_id not in settings.admin_ids_list and user_id != settings.SUPER_ADMIN_ID:
        raise HTTPException(status_code=403, detail="Access denied")
    return user_id
