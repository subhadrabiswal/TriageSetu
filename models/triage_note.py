"""
models/triage_note.py
------------------------
The AI-drafted, structured summary of a patient's case. This is the
main artifact a reviewer (nurse/doctor) looks at. It is always
non-diagnostic - see risk_rationale_text for *why* a tag was chosen,
so nothing here is a black box.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Text, Float, JSON, ForeignKey

from app.database import Base


class RiskCategory(str, enum.Enum):
    RED = "red"        # emergency - see immediately
    YELLOW = "yellow"  # urgent - priority review
    GREEN = "green"    # routine


class TriageStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ESCALATED = "escalated"
    REJECTED = "rejected"


class TriageNote(Base):
    __tablename__ = "triage_notes"

    triage_note_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    timeline_json = Column(JSON, nullable=True)
    missing_info_json = Column(JSON, nullable=True)
    follow_up_questions_json = Column(JSON, nullable=True)
    risk_category = Column(Enum(RiskCategory), nullable=False)
    risk_score = Column(Float, nullable=True)
    risk_rationale_text = Column(Text, nullable=True)
    status = Column(Enum(TriageStatus), default=TriageStatus.DRAFT)
    generated_at = Column(DateTime, default=datetime.utcnow)
