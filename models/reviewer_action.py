"""
models/reviewer_action.py
----------------------------
Records what a human reviewer did with a triage note - this is the
human-in-the-loop trail that shows a person, not just the AI, made
the final call.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Text, ForeignKey

from app.database import Base


class ReviewerActionType(str, enum.Enum):
    APPROVED = "approved"
    EDITED = "edited"
    ESCALATED = "escalated"
    REJECTED = "rejected"


class ReviewerAction(Base):
    __tablename__ = "reviewer_actions"

    action_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    triage_note_id = Column(String, ForeignKey("triage_notes.triage_note_id"), nullable=False)
    reviewer_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    action_type = Column(Enum(ReviewerActionType), nullable=False)
    comments = Column(Text, nullable=True)
    edited_summary_text = Column(Text, nullable=True)
    action_timestamp = Column(DateTime, default=datetime.utcnow)
