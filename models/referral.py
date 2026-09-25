"""
models/referral.py
---------------------
A referral note prepared when a reviewer escalates a case to a
higher-level facility.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Text, ForeignKey

from app.database import Base


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"


class Referral(Base):
    __tablename__ = "referrals"

    referral_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    triage_note_id = Column(String, ForeignKey("triage_notes.triage_note_id"), nullable=False)
    referred_to_facility_name = Column(String, nullable=False)
    referral_reason = Column(Text, nullable=True)
    referral_note_text = Column(Text, nullable=True)
    created_by = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
