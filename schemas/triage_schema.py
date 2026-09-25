from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.triage_note import RiskCategory, TriageStatus


class GenerateTriageRequest(BaseModel):
    patient_id: str


class EvidenceItem(BaseModel):
    symptom: str
    source_snippet: str


class TriageNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    triage_note_id: str
    patient_id: str
    summary_text: str
    timeline_json: Any
    missing_info_json: Any
    follow_up_questions_json: Any
    risk_category: RiskCategory
    risk_score: float | None
    risk_rationale_text: str | None
    status: TriageStatus
    generated_at: datetime
    evidence: list[EvidenceItem] = []
