"""
models/user.py
---------------
Represents a staff member who logs into the system: a health worker,
nurse, doctor, or admin at a specific facility.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, ForeignKey

from app.database import Base


class UserRole(str, enum.Enum):
    PATIENT = "patient"
    HEALTH_WORKER = "health_worker"
    NURSE = "nurse"
    DOCTOR = "doctor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), nullable=False)
    preferred_language = Column(String, default="en")
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
