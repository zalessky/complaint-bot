from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db import crud
from backend.core.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class AuthResponse(BaseModel):
    user_id: int
    telegram_id: int
    username: str = None
    first_name: str = None
    is_admin: bool = False
    role: str = "user"

@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_telegram_id(db, current_user)
    if not user:
        user = await crud.create_user(db, current_user)
    
    employee = await crud.get_employee_by_telegram_id(db, current_user)
    
    return AuthResponse(
        user_id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        is_admin=employee is not None,
        role=employee.role if employee else "user"
    )
