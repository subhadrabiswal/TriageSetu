from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.consent_record import ConsentType


class ConsentCreate(BaseModel):
    patient_id: str
    consent_type: ConsentType
    granted: bool
    retention_period_days: int = 90


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consent_id: str
    patient_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime
    retention_period_days: int
