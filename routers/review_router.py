"""
routers/review_router.py
----------------------------
Where a nurse or doctor turns an AI draft into a reviewed decision.
Supports: approve, edit, escalate (referral generation), and reject actions.
Logs an immutable entry to audit_logs for every action taken.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.triage_note import TriageNote, TriageStatus
from app.models.reviewer_action import ReviewerAction, ReviewerActionType
from app.models.facility_queue import FacilityQueue, QueueStatus
from app.models.referral import Referral, ReferralStatus
from app.models.user import User
from app.schemas.review_schema import ReviewActionRequest, ReviewerActionOut
from app.middleware.auth_middleware import require_roles
from app.utils.rbac import REVIEWER_ROLES
from app.services import audit_service

router = APIRouter(prefix="/triage-notes", tags=["review"])

_STATUS_BY_ACTION = {
    ReviewerActionType.APPROVED: TriageStatus.APPROVED,
    ReviewerActionType.EDITED: TriageStatus.APPROVED,
    ReviewerActionType.ESCALATED: TriageStatus.ESCALATED,
    ReviewerActionType.REJECTED: TriageStatus.REJECTED,
}


@router.patch("/{triage_note_id}/review", response_model=ReviewerActionOut)
def review_triage_note(
    triage_note_id: str,
    payload: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*REVIEWER_ROLES)),
):
    note = db.query(TriageNote).filter(TriageNote.triage_note_id == triage_note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Triage note not found")

    # Apply edits if action is EDITED
    if payload.action_type == ReviewerActionType.EDITED:
        if payload.edited_summary_text:
            note.summary_text = payload.edited_summary_text
        if payload.edited_risk_category:
            note.risk_category = payload.edited_risk_category

    note.status = _STATUS_BY_ACTION[payload.action_type]
    db.commit()

    # Log reviewer action
    action = ReviewerAction(
        triage_note_id=triage_note_id,
        reviewer_id=current_user.user_id,
        action_type=payload.action_type,
        comments=payload.comments,
        edited_summary_text=payload.edited_summary_text,
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    # Auto-create referral draft if escalated
    if payload.action_type == ReviewerActionType.ESCALATED:
        existing_ref = db.query(Referral).filter(Referral.triage_note_id == triage_note_id).first()
        if not existing_ref:
            referral = Referral(
                patient_id=note.patient_id,
                triage_note_id=triage_note_id,
                referred_to_facility_name="District General Hospital / Specialist Center",
                referral_reason=payload.comments or "Escalated by reviewer for specialist care",
                referral_note_text=f"REFERRED CASE: {note.summary_text}",
                created_by=current_user.user_id,
                status=ReferralStatus.PENDING,
            )
            db.add(referral)
            db.commit()

    # Update Queue Status
    queue_entry = (
        db.query(FacilityQueue)
        .filter(FacilityQueue.patient_id == note.patient_id)
        .filter(FacilityQueue.status != QueueStatus.COMPLETED)
        .first()
    )
    if queue_entry:
        queue_entry.status = (
            QueueStatus.WAITING if payload.action_type == ReviewerActionType.REJECTED
            else QueueStatus.COMPLETED
        )
        db.commit()

    role_val = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    audit_service.log_user_activity(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
        role=role_val,
        action=f"CLINICAL_CASE_{payload.action_type.value.upper()}",
        entity_type="triage_note",
        entity_id=triage_note_id,
        metadata={"reviewer_role": role_val, "comments": payload.comments}
    )

    return action

