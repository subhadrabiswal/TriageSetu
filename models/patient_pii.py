"""
models/patient_pii.py
-----------------------
Keeps identifying details (name, contact number) separate from the
clinical patient record. Only the roles listed in access_restricted_to
should ever be shown this data - everything else in the system works
off the anonymized_token in patient.py instead.
"""

import uuid

from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, JSON, DateTime

from app.database import Base


class PatientPII(Base):
    __tablename__ = "patient_contact_pii"

    pii_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    anonymized_token = Column(String, ForeignKey("patients.anonymized_token"), unique=True, nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), unique=True, nullable=True)
    encrypted_name = Column(String, nullable=True)
    encrypted_contact_number = Column(String, nullable=True)
    # List of role names (e.g. ["admin", "doctor"]) allowed to view this record.
    access_restricted_to = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
