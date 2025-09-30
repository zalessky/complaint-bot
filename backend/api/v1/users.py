from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db import crud
from backend.core.dependencies import get_admin_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str = None
    first_name: str = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user(
    telegram_id: int,
    current_user: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_user_by_telegram_id(db, telegram_id)
