"""
models/symptom_report.py
--------------------------
One text or voice symptom submission from a patient.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Text, ForeignKey

from app.database import Base


class InputMode(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"


class SymptomReport(Base):
    __tablename__ = "symptom_reports"

    report_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    input_mode = Column(Enum(InputMode), nullable=False)
    raw_input_text = Column(Text, nullable=False)
    detected_language = Column(String, nullable=True)
    translated_text_en = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
