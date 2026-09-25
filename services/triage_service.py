"""
services/triage_service.py
------------------------------
The main orchestrator for "generate a triage note": gathers a
patient's latest symptom report and any uploaded documents, runs the
AI/rules layer, persists the result, queues the patient, and writes
an audit entry. Routers call this one function rather than wiring
five services together themselves.
"""

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.symptom_report import SymptomReport
from app.models.document import UploadedDocument
from app.models.triage_note import TriageNote, TriageStatus
from app.services import summarization_service, queue_service, audit_service


def generate_for_patient(db: Session, patient_id: str, triggered_by_user_id: str | None = None):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if patient is None:
        raise ValueError("Patient not found")

    latest_symptom = (
        db.query(SymptomReport)
        .filter(SymptomReport.patient_id == patient_id)
        .order_by(SymptomReport.submitted_at.desc())
        .first()
    )
    if latest_symptom is None:
        raise ValueError("No symptom report found for this patient yet")

    documents = db.query(UploadedDocument).filter(UploadedDocument.patient_id == patient_id).all()
    ocr_text_combined = "\n".join(d.ocr_extracted_text for d in documents if d.ocr_extracted_text)

    language = latest_symptom.detected_language or patient.preferred_language or "en"
    draft = summarization_service.build_triage_draft(
        raw_text=latest_symptom.raw_input_text,
        ocr_text=ocr_text_combined,
        language=language,
    )

    triage_note = TriageNote(
        patient_id=patient_id,
        summary_text=draft["summary_text"],
        timeline_json=draft["timeline_json"],
        missing_info_json=draft["missing_info_json"],
        follow_up_questions_json=draft["follow_up_questions_json"],
        risk_category=draft["risk_category"],
        risk_score=draft["risk_score"],
        risk_rationale_text=draft["risk_rationale_text"],
        status=TriageStatus.UNDER_REVIEW,
    )
    db.add(triage_note)
    db.commit()
    db.refresh(triage_note)

    queue_service.add_to_queue(db, patient_id, patient.facility_id, draft["risk_category"])

    audit_service.log(
        db,
        action_type="AI_SUMMARY_GENERATED",
        entity_type="triage_note",
        entity_id=triage_note.triage_note_id,
        user_id=triggered_by_user_id,
        metadata={"extraction_source": draft["extraction_source"]},
    )

    return triage_note, draft["evidence"]
