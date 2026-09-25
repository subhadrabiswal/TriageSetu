"""
routers/symptom_router.py
-----------------------------
Text and voice symptom intake. Voice is already transcribed to text
in the browser before it reaches this endpoint (see stt_service.py
for why), so both input modes share the same request shape.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.symptom_report import SymptomReport
from app.models.user import User
from app.schemas.symptom_schema import (
    SymptomCreate, SymptomOut, SuggestQuestionsRequest, SuggestQuestionsResponse
)
from app.middleware.auth_middleware import require_roles
from app.utils.rbac import INTAKE_ROLES
from pydantic import BaseModel
from app.services.translation_service import translate_to_english, translate_text_bhashini
from app.services import audit_service
from app.ai.structured_extraction import extract
from app.services.followup_service import dedupe_questions

router = APIRouter(prefix="/symptoms", tags=["symptoms"])


class TranslateRequest(BaseModel):
    text: str
    source_language: str = "hi"
    target_language: str = "en"


@router.post("/translate")
def translate_symptom_text(payload: TranslateRequest):
    if not payload.text or not payload.text.strip():
        return {"translated_text": payload.text, "original_text": payload.text}

    translated = translate_text_bhashini(
        payload.text,
        source_language=payload.source_language,
        target_language=payload.target_language
    )
    return {
        "translated_text": translated,
        "original_text": payload.text,
        "source_language": payload.source_language,
        "target_language": payload.target_language
    }


@router.post("/suggest-questions", response_model=SuggestQuestionsResponse)
def suggest_questions(payload: SuggestQuestionsRequest):
    if not payload.raw_input_text or not payload.raw_input_text.strip():
        return SuggestQuestionsResponse(questions=[], missing_info=[])

    extraction = extract(payload.raw_input_text, None, payload.language or "en")
    questions = dedupe_questions(extraction.get("follow_up_questions", []))
    missing_info = extraction.get("missing_info", [])

    return SuggestQuestionsResponse(questions=questions, missing_info=missing_info)


@router.post("", response_model=SymptomOut, status_code=201)
def submit_symptoms(
    payload: SymptomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*INTAKE_ROLES)),
):
    patient = db.query(Patient).filter(Patient.patient_id == payload.patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    language = payload.detected_language or patient.preferred_language or "en"
    translation = translate_to_english(payload.raw_input_text, language)

    report = SymptomReport(
        patient_id=payload.patient_id,
        input_mode=payload.input_mode,
        raw_input_text=payload.raw_input_text,
        detected_language=language,
        translated_text_en=translation["translated_text"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    audit_service.log(
        db, action_type="SYMPTOM_REPORT_SUBMITTED", entity_type="symptom_report",
        entity_id=report.report_id, user_id=current_user.user_id,
    )

    return report
