from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.symptom_report import InputMode


class SymptomCreate(BaseModel):
    patient_id: str
    input_mode: InputMode
    raw_input_text: str
    detected_language: str | None = "en"


class SuggestQuestionsRequest(BaseModel):
    raw_input_text: str
    language: str | None = "en"


class SuggestQuestionsResponse(BaseModel):
    questions: list[str]
    missing_info: list[str]


class SymptomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    patient_id: str
    input_mode: InputMode
    raw_input_text: str
    detected_language: str | None
    translated_text_en: str | None
    submitted_at: datetime
