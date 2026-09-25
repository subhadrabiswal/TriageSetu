"""
models/patient.py
-------------------
The core patient record. Notice there is NO name or contact number
here on purpose - identifying details live separately in
patient_pii.py so that most of the system only ever sees an
anonymized token, not who the patient actually is.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Date, Boolean, ForeignKey

from app.database import Base


class AgeRange(str, enum.Enum):
    CHILD = "0-12"
    TEEN = "13-18"
    ADULT = "19-40"
    MIDDLE_AGED = "41-60"
    SENIOR = "60+"


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    anonymized_token = Column(String, unique=True, nullable=False)
    age_range = Column(String, nullable=True)
    gender = Column(String, nullable=True)  # self-reported, optional
    facility_id = Column(String, ForeignKey("facilities.facility_id"), nullable=False)
    preferred_language = Column(String, default="en")
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime, nullable=True)
    data_retention_expiry = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
