"""
models/facility_queue.py
----------------------------
The prioritized waiting queue for a facility. priority_rank is
derived from the triage note's risk_category - the logic for
computing it will live in services/queue_service.py in a later phase.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey

from app.database import Base


class QueueStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"


class FacilityQueue(Base):
    __tablename__ = "facility_queue"

    queue_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), nullable=False)
    priority_rank = Column(Integer, nullable=True)
    status = Column(Enum(QueueStatus), default=QueueStatus.WAITING)
    entered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
