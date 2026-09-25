"""
routers/referral_router.py
------------------------------
Creates a referral note. Only allowed once a triage note has already
been through review - referring an un-reviewed AI draft would skip
the human-in-the-loop step entirely.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.triage_note import TriageNote, TriageStatus
from app.models.user import User
from app.schemas.referral_schema import ReferralCreate, ReferralOut
from app.middleware.auth_middleware import require_roles
from app.utils.rbac import REVIEWER_ROLES
from app.services.referral_service import create_referral
from app.services import audit_service

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.post("", response_model=ReferralOut, status_code=201)
def create_referral_note(
    payload: ReferralCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*REVIEWER_ROLES)),
):
    note = db.query(TriageNote).filter(TriageNote.triage_note_id == payload.triage_note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Triage note not found")
    if note.status not in (TriageStatus.APPROVED, TriageStatus.ESCALATED):
        raise HTTPException(
            status_code=400,
            detail="Triage note must be reviewed (approved or escalated) before a referral can be created",
        )

    referral = create_referral(
        db, payload.patient_id, note, payload.referred_to_facility_name,
        payload.referral_reason, current_user.user_id,
    )

    audit_service.log(
        db, action_type="REFERRAL_CREATED", entity_type="referral",
        entity_id=referral.referral_id, user_id=current_user.user_id,
    )

    return referral
