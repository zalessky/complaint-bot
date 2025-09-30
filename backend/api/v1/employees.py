from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db import crud
from backend.core.dependencies import get_current_user
from backend.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class EmployeeCreate(BaseModel):
    telegram_id: int
    full_name: str
    role: str = "operator"

class EmployeeResponse(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user != settings.SUPER_ADMIN_ID:
        raise HTTPException(status_code=403, detail="Super admin only")
    
    employee = await crud.create_employee(db, employee_data.telegram_id, employee_data.full_name, employee_data.role)
    return employee
