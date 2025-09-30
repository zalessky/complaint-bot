from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.core.config import settings
from backend.core.security import get_current_user_id

async def get_current_user(
    x_telegram_init_data: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> int:
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing auth data")
    try:
        return get_current_user_id(x_telegram_init_data, settings.BOT_TOKEN)
    except:
        raise HTTPException(status_code=401, detail="Auth failed")

async def get_admin_user(current_user: int = Depends(get_current_user)) -> int:
    if current_user not in settings.admin_ids_list and current_user != settings.SUPER_ADMIN_ID:
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user
