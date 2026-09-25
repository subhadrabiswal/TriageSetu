"""
routers/triage_router.py
----------------------------
Generates and fetches triage notes. Generation is intentionally its
own explicit action (not automatic on every symptom submission) so a
health worker can attach a document first if there is one.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.triage_note import TriageNote
from app.models.user import User
from app.schemas.triage_schema import GenerateTriageRequest, TriageNoteOut, EvidenceItem
from app.middleware.auth_middleware import get_current_user, require_roles
from app.utils.rbac import INTAKE_ROLES
from app.services import triage_service

router = APIRouter(prefix="/triage-notes", tags=["triage"])


@router.post("/generate", response_model=TriageNoteOut, status_code=201)
def generate_triage_note(
    payload: GenerateTriageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*INTAKE_ROLES)),
):
    try:
        triage_note, evidence = triage_service.generate_for_patient(
            db, payload.patient_id, triggered_by_user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    result = TriageNoteOut.model_validate(triage_note)
    result.evidence = [EvidenceItem(**item) for item in evidence]
    return result


@router.get("/{triage_note_id}", response_model=TriageNoteOut)
def get_triage_note(triage_note_id: str, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    note = db.query(TriageNote).filter(TriageNote.triage_note_id == triage_note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Triage note not found")
    return note
