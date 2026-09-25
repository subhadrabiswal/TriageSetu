"""
models/audit_log.py
-----------------------
An immutable trail of every important action - both AI-generated
steps and human decisions - for accountability and auditing.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Nullable because some actions (like an AI auto-summary) are
    # triggered by the system itself, not a logged-in user.
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    action_type = Column(String, nullable=False)   # e.g. "AI_SUMMARY_GENERATED"
    entity_type = Column(String, nullable=False)   # e.g. "triage_note"
    entity_id = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
