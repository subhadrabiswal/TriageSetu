"""
routers/patient_router.py
-----------------------------
Patient creation, timestamped consent capture, PII isolation vault management,
and RBAC-protected PII retrieval.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.patient_pii import PatientPII
from app.models.consent_record import ConsentRecord, ConsentType
from app.models.user import User, UserRole
from app.schemas.patient_schema import PatientCreate, PatientOut, PatientPIIOut
from app.schemas.consent_schema import ConsentCreate, ConsentOut
from app.middleware.auth_middleware import require_roles, get_current_user
from app.utils.anonymization import generate_anonymized_token
from app.utils.rbac import INTAKE_ROLES, PII_ACCESS_ROLES
from app.utils.pii_encryption import encrypt_pii, decrypt_pii
from app.services import audit_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*INTAKE_ROLES)),
):
    if not payload.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register a patient without explicit consent",
        )

    now = datetime.utcnow()
    token = generate_anonymized_token(payload.facility_id)

    # 1. Save isolated clinical patient record (NO PII fields stored here)
    patient = Patient(
        anonymized_token=token,
        age_range=payload.age_range,
        gender=payload.gender,
        facility_id=payload.facility_id,
        preferred_language=payload.preferred_language,
        consent_given=True,
        consent_timestamp=now,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # 2. Store PII (name, phone) encrypted in separate vault table patient_contact_pii
    if payload.name or payload.contact_number:
        pii_entry = PatientPII(
            anonymized_token=patient.anonymized_token,
            patient_id=patient.patient_id,
            encrypted_name=encrypt_pii(payload.name),
            encrypted_contact_number=encrypt_pii(payload.contact_number),
            access_restricted_to=["doctor", "admin"],
            created_at=now,
        )
        db.add(pii_entry)

    # 3. Save timestamped consent records
    consent_data = ConsentRecord(
        patient_id=patient.patient_id,
        consent_type=ConsentType.DATA_COLLECTION,
        granted=True,
        granted_at=now,
    )
    consent_ai = ConsentRecord(
        patient_id=patient.patient_id,
        consent_type=ConsentType.AI_PROCESSING,
        granted=True,
        granted_at=now,
    )
    db.add_all([consent_data, consent_ai])
    db.commit()

    # 4. Write immutable audit log entries
    audit_service.log(
        db,
        action_type="PATIENT_REGISTERED",
        entity_type="patient",
        entity_id=patient.patient_id,
        user_id=current_user.user_id,
        metadata={"anonymized_token": patient.anonymized_token},
    )
    audit_service.log(
        db,
        action_type="CONSENT_RECORDED",
        entity_type="consent_record",
        entity_id=consent_data.consent_id,
        user_id=current_user.user_id,
        metadata={"consent_types": ["data_collection", "ai_processing"], "timestamp": now.isoformat()},
    )

    return patient


@router.post("/{patient_id}/consent", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
def record_patient_consent(
    patient_id: str,
    payload: ConsentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    now = datetime.utcnow()
    consent = ConsentRecord(
        patient_id=patient.patient_id,
        consent_type=payload.consent_type,
        granted=payload.granted,
        granted_at=now,
        retention_period_days=payload.retention_period_days,
    )
    db.add(consent)

    patient.consent_given = payload.granted
    patient.consent_timestamp = now
    db.commit()
    db.refresh(consent)

    audit_service.log(
        db,
        action_type="CONSENT_RECORDED",
        entity_type="consent_record",
        entity_id=consent.consent_id,
        user_id=current_user.user_id,
        metadata={"consent_type": payload.consent_type.value, "granted": payload.granted, "timestamp": now.isoformat()},
    )

    return consent


@router.get("/{identifier}/pii", response_model=PatientPIIOut)
def get_patient_pii(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Strict RBAC check: only DOCTOR and ADMIN can access decrypted PII
    if current_user.role not in PII_ACCESS_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Role '{current_user.role.value}' is not authorized to access patient contact PII vault",
        )

    # Search by anonymized_token or patient_id
    pii_record = (
        db.query(PatientPII)
        .filter((PatientPII.anonymized_token == identifier) | (PatientPII.patient_id == identifier))
        .first()
    )

    if not pii_record:
        # Check if patient exists
        patient = (
            db.query(Patient)
            .filter((Patient.anonymized_token == identifier) | (Patient.patient_id == identifier))
            .first()
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient record not found")
        return PatientPIIOut(
            anonymized_token=patient.anonymized_token,
            patient_id=patient.patient_id,
            name=None,
            contact_number=None,
            access_restricted_to=["doctor", "admin"],
        )

    decrypted_name = decrypt_pii(pii_record.encrypted_name)
    decrypted_phone = decrypt_pii(pii_record.encrypted_contact_number)

    audit_service.log(
        db,
        action_type="PII_ACCESSED",
        entity_type="patient_contact_pii",
        entity_id=pii_record.pii_id,
        user_id=current_user.user_id,
        metadata={"anonymized_token": pii_record.anonymized_token},
    )

    return PatientPIIOut(
        anonymized_token=pii_record.anonymized_token,
        patient_id=pii_record.patient_id or identifier,
        name=decrypted_name,
        contact_number=decrypted_phone,
        access_restricted_to=pii_record.access_restricted_to or ["doctor", "admin"],
    )


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = (
        db.query(Patient)
        .filter((Patient.patient_id == patient_id) | (Patient.anonymized_token == patient_id))
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/{patient_id}/answers")
def save_patient_followup_answers(
    patient_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.followup_answer import FollowUpAnswer

    patient = (
        db.query(Patient)
        .filter((Patient.patient_id == patient_id) | (Patient.anonymized_token == patient_id))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    answers_list = payload.get("answers", [])
    for item in answers_list:
        q = item.get("question")
        a = item.get("answer")
        if q and a:
            db_answer = FollowUpAnswer(
                patient_id=patient.patient_id,
                question=q,
                answer=a
            )
            db.add(db_answer)

    db.commit()

    role_val = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    audit_service.log_user_activity(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
        role=role_val,
        action="PATIENT_FOLLOWUP_ANSWERS_SAVED",
        entity_type="patient",
        entity_id=patient.patient_id,
        metadata={"count": len(answers_list)}
    )

    return {"status": "success", "message": "Follow-up answers saved successfully for the patient."}


@router.get("/{patient_id}/summary")
def get_patient_case_summary(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.followup_answer import FollowUpAnswer
    from app.models.symptom_report import SymptomReport
    from app.models.triage_note import TriageNote
    from app.models.patient_pii import PatientPII
    from app.utils.pii_encryption import decrypt_pii

    patient = (
        db.query(Patient)
        .filter((Patient.patient_id == patient_id) | (Patient.anonymized_token == patient_id))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get symptoms
    symptom_report = (
        db.query(SymptomReport)
        .filter(SymptomReport.patient_id == patient.patient_id)
        .order_by(SymptomReport.created_at.desc())
        .first()
    )

    # Get triage note
    triage_note = (
        db.query(TriageNote)
        .filter(TriageNote.patient_id == patient.patient_id)
        .order_by(TriageNote.created_at.desc())
        .first()
    )

    # Get decrypted PII if allowed
    patient_name = patient.anonymized_token
    pii_entry = db.query(PatientPII).filter(PatientPII.patient_id == patient.patient_id).first()
    if pii_entry and pii_entry.encrypted_name:
        try:
            patient_name = decrypt_pii(pii_entry.encrypted_name) or patient.anonymized_token
        except Exception:
            pass

    answers = (
        db.query(FollowUpAnswer)
        .filter(FollowUpAnswer.patient_id == patient.patient_id)
        .order_by(FollowUpAnswer.created_at.asc())
        .all()
    )

    risk_cat = triage_note.risk_category.value if (triage_note and hasattr(triage_note.risk_category, 'value')) else (triage_note.risk_category if triage_note else "green")

    return {
        "patient_id": patient.patient_id,
        "anonymized_token": patient.anonymized_token,
        "name": patient_name,
        "symptoms": symptom_report.raw_input_text if symptom_report else "No symptoms recorded",
        "risk_category": risk_cat,
        "risk_score": triage_note.risk_score if triage_note else 0.5,
        "summary_text": triage_note.summary_text if triage_note else (symptom_report.raw_input_text if symptom_report else "Patient intake completed."),
        "risk_rationale_text": triage_note.risk_rationale_text if triage_note else "",
        "followup_qa": [{"question": a.question, "answer": a.answer} for a in answers],
        "follow_up_questions_json": [a.question for a in answers] if answers else (triage_note.follow_up_questions_json if triage_note else []),
    }


@router.get("", response_model=list[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Patient)
        .filter(Patient.facility_id == current_user.facility_id)
        .order_by(Patient.created_at.desc())
        .limit(100)
        .all()
    )

