from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    complaints = relationship("Complaint", back_populates="user")

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default='operator')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    assignments = relationship("Assignment", back_populates="employee")

class Complaint(Base):
    __tablename__ = 'complaints'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    type = Column(String(50), default='complaint')
    description = Column(Text, nullable=False)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    photos = Column(Text)
    status = Column(String(50), default='new', index=True)
    priority = Column(String(20), default='medium')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    user = relationship("User", back_populates="complaints")
    assignments = relationship("Assignment", back_populates="complaint")
    comments = relationship("Comment", back_populates="complaint")

class Assignment(Base):
    __tablename__ = 'assignments'
    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    complaint = relationship("Complaint", back_populates="assignments")
    employee = relationship("Employee", back_populates="assignments")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id'))
    author_id = Column(Integer, nullable=False)
    author_type = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_internal = Column(Boolean, default=False)
    complaint = relationship("Complaint", back_populates="comments")
