from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.db.models import User, Employee, Complaint, Assignment, Comment
from typing import List, Optional
from datetime import datetime

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, telegram_id: int, username: str = None, first_name: str = None) -> User:
    user = User(telegram_id=telegram_id, username=username, first_name=first_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_complaint(db: AsyncSession, user_id: int, category: str, description: str, **kwargs) -> Complaint:
    complaint = Complaint(user_id=user_id, category=category, description=description, **kwargs)
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint

async def get_complaints_by_user(db: AsyncSession, user_id: int) -> List[Complaint]:
    result = await db.execute(
        select(Complaint).where(Complaint.user_id == user_id).order_by(desc(Complaint.created_at))
    )
    return result.scalars().all()

async def get_complaint_by_id(db: AsyncSession, complaint_id: int) -> Optional[Complaint]:
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    return result.scalar_one_or_none()

async def update_complaint_status(db: AsyncSession, complaint_id: int, new_status: str) -> Complaint:
    complaint = await get_complaint_by_id(db, complaint_id)
    if complaint:
        complaint.status = new_status
        complaint.updated_at = datetime.utcnow()
        if new_status == 'resolved':
            complaint.resolved_at = datetime.utcnow()
        await db.commit()
        await db.refresh(complaint)
    return complaint

async def get_all_complaints(db: AsyncSession, status: str = None) -> List[Complaint]:
    query = select(Complaint).order_by(desc(Complaint.created_at))
    if status:
        query = query.where(Complaint.status == status)
    result = await db.execute(query)
    return result.scalars().all()

async def get_employee_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[Employee]:
    result = await db.execute(select(Employee).where(Employee.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def create_employee(db: AsyncSession, telegram_id: int, full_name: str, role: str = 'operator') -> Employee:
    employee = Employee(telegram_id=telegram_id, full_name=full_name, role=role)
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee

async def create_comment(db: AsyncSession, complaint_id: int, author_id: int, author_type: str, text: str, is_internal: bool = False) -> Comment:
    comment = Comment(complaint_id=complaint_id, author_id=author_id, author_type=author_type, text=text, is_internal=is_internal)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment

async def get_comments_by_complaint(db: AsyncSession, complaint_id: int, include_internal: bool = False) -> List[Comment]:
    query = select(Comment).where(Comment.complaint_id == complaint_id)
    if not include_internal:
        query = query.where(Comment.is_internal == False)
    query = query.order_by(Comment.created_at)
    result = await db.execute(query)
    return result.scalars().all()
