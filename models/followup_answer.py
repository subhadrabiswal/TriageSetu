"""
models/followup_answer.py
-----------------------------
Persists AI-generated follow-up questions and patient answers
linked to a specific patient_id.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey

from app.database import Base


class FollowUpAnswer(Base):
    __tablename__ = "followup_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
