"""
models/document.py
--------------------
An uploaded file (lab report, prescription photo, or scan) along with
whatever text OCR was able to pull out of it.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime, Text, Float, ForeignKey

from app.database import Base


class DocumentType(str, enum.Enum):
    LAB_REPORT = "lab_report"
    PRESCRIPTION = "prescription"
    SCAN_IMAGE = "scan_image"
    OTHER = "other"


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    document_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_reference = Column(String, nullable=False)  # path or storage key
    ocr_extracted_text = Column(Text, nullable=True)
    ocr_confidence_score = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
