"""
models/consent_record.py
----------------------------
A record of exactly what a patient consented to, and when. Required
before any data collection or AI processing happens.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, Boolean, DateTime, Integer, ForeignKey

from app.database import Base


class ConsentType(str, enum.Enum):
    DATA_COLLECTION = "data_collection"
    AI_PROCESSING = "ai_processing"
    DATA_SHARING_REFERRAL = "data_sharing_referral"


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    consent_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    consent_type = Column(Enum(ConsentType), nullable=False)
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    retention_period_days = Column(Integer, default=90)
