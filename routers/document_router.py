"""
routers/document_router.py
------------------------------
Handles report/prescription photo uploads. Files are saved to the
local uploads/ folder (see UPLOAD_DIR in config.py) and immediately
run through OCR so the extracted text is available right away for
the reviewer and for triage-note generation.
"""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.document import UploadedDocument, DocumentType
from app.models.user import User
from app.schemas.document_schema import DocumentOut
from app.middleware.auth_middleware import require_roles
from app.utils.rbac import INTAKE_ROLES
from app.services.ocr_service import extract_text
from app.services import audit_service
from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=201)
def upload_document(
    patient_id: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*INTAKE_ROLES)),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    extension = os.path.splitext(file.filename or "")[1] or ".jpg"
    stored_name = f"{uuid.uuid4()}{extension}"
    stored_path = os.path.join(upload_dir, stored_name)

    with open(stored_path, "wb") as out_file:
        out_file.write(file.file.read())

    ocr_result = extract_text(stored_path)

    ocr_text = ocr_result["text"] or ocr_result["error"] or "No text detected in the uploaded file."
    document = UploadedDocument(
        patient_id=patient_id,
        document_type=document_type,
        file_reference=stored_name,
        ocr_extracted_text=ocr_text,
        ocr_confidence_score=ocr_result["confidence"],
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    audit_service.log(
        db, action_type="DOCUMENT_UPLOADED", entity_type="uploaded_document",
        entity_id=document.document_id, user_id=current_user.user_id,
    )

    return document
