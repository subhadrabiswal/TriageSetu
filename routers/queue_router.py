"""
routers/queue_router.py
---------------------------
Returns the reviewer's prioritized worklist for their own facility.
Each row is enriched with the patient's anonymized token and the
most recent triage note's risk category and a short chief-complaint
snippet, so the frontend can render the queue in one call.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.triage_note import TriageNote
from app.models.user import User
from app.schemas.queue_schema import QueueItemOut
from app.middleware.auth_middleware import get_current_user
from app.services import queue_service

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_model=list[QueueItemOut])
def get_facility_queue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = queue_service.get_queue(db, current_user.facility_id)

    results = []
    for entry in entries:
        patient = db.query(Patient).filter(Patient.patient_id == entry.patient_id).first()
        latest_note = (
            db.query(TriageNote)
            .filter(TriageNote.patient_id == entry.patient_id)
            .order_by(TriageNote.generated_at.desc())
            .first()
        )
        results.append(QueueItemOut(
            queue_id=entry.queue_id,
            patient_id=entry.patient_id,
            facility_id=entry.facility_id,
            anonymized_token=patient.anonymized_token if patient else "UNKNOWN",
            triage_note_id=latest_note.triage_note_id if latest_note else None,
            priority_rank=entry.priority_rank,
            status=entry.status,
            risk_category=latest_note.risk_category if latest_note else None,
            chief_complaint=(latest_note.summary_text[:100] if latest_note else None),
            entered_at=entry.entered_at,
            updated_at=entry.updated_at,
        ))
    return results
