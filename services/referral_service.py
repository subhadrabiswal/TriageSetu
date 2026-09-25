"""
services/referral_service.py
--------------------------------
Builds a referral note from an already-reviewed triage note. The
note is templated (not free-form LLM text) so its content is always
traceable straight back to what the reviewer approved.
"""

from sqlalchemy.orm import Session

from app.models.referral import Referral, ReferralStatus
from app.models.triage_note import TriageNote


def build_referral_note_text(triage_note: TriageNote, reason: str | None) -> str:
    lines = [
        "REFERRAL NOTE (auto-drafted from reviewed triage note - verify before sending)",
        "",
        f"Risk category at referral: {triage_note.risk_category.value.upper()}",
        f"Summary: {triage_note.summary_text}",
    ]
    if reason:
        lines.append(f"Reason for referral: {reason}")
    if triage_note.risk_rationale_text:
        lines.append(f"Risk rationale: {triage_note.risk_rationale_text}")
    lines.append("")
    lines.append("This is a triage-support note, not a diagnosis. Receiving facility should conduct its own assessment.")
    return "\n".join(lines)


def create_referral(db: Session, patient_id: str, triage_note: TriageNote,
                     referred_to_facility_name: str, reason: str | None,
                     created_by: str) -> Referral:
    referral = Referral(
        patient_id=patient_id,
        triage_note_id=triage_note.triage_note_id,
        referred_to_facility_name=referred_to_facility_name,
        referral_reason=reason,
        referral_note_text=build_referral_note_text(triage_note, reason),
        created_by=created_by,
        status=ReferralStatus.PENDING,
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral
