from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db import crud
from backend.core.dependencies import get_current_user, get_admin_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ComplaintCreate(BaseModel):
    category: str
    description: str
    type: str = "complaint"
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photos: Optional[str] = None
    priority: str = "medium"

class ComplaintResponse(BaseModel):
    id: int
    category: str
    description: str
    type: str
    status: str
    priority: str
    address: Optional[str]
    photos: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintStatusUpdate(BaseModel):
    status: str

@router.post("/", response_model=ComplaintResponse)
async def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_telegram_id(db, current_user)
    if not user:
        user = await crud.create_user(db, current_user)
    
    complaint = await crud.create_complaint(db, user.id, **complaint_data.model_dump())
    return complaint

@router.get("/my", response_model=List[ComplaintResponse])
async def get_my_complaints(
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_telegram_id(db, current_user)
    if not user:
        return []
    return await crud.get_complaints_by_user(db, user.id)

@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: int,
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    complaint = await crud.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Not found")
    return complaint

@router.get("/", response_model=List[ComplaintResponse])
async def get_all_complaints(
    status: Optional[str] = None,
    current_user: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_all_complaints(db, status)

@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
async def update_complaint_status_endpoint(
    complaint_id: int,
    status_update: ComplaintStatusUpdate,
    current_user: int = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    complaint = await crud.update_complaint_status(db, complaint_id, status_update.status)
    if not complaint:
        raise HTTPException(status_code=404, detail="Not found")
    return complaint
