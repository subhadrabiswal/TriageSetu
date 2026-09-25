from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.patient import AgeRange


class PatientCreate(BaseModel):
    facility_id: str
    age_range: str | None = None
    gender: str | None = None
    preferred_language: str = "en"
    consent_given: bool = True
    name: str | None = None
    contact_number: str | None = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    anonymized_token: str
    age_range: str | None = None
    gender: str | None = None
    facility_id: str
    preferred_language: str
    consent_given: bool
    consent_timestamp: datetime | None = None
    created_at: datetime


class PatientPIIOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anonymized_token: str
    patient_id: str
    name: str | None = None
    contact_number: str | None = None
    access_restricted_to: list[str] = ["doctor", "admin"]

