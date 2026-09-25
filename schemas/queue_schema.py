from datetime import datetime

from pydantic import BaseModel

from app.models.facility_queue import QueueStatus
from app.models.triage_note import RiskCategory


class QueueItemOut(BaseModel):
    queue_id: str
    patient_id: str
    facility_id: str
    anonymized_token: str
    triage_note_id: str | None = None
    priority_rank: int | None
    status: QueueStatus
    risk_category: RiskCategory | None = None
    chief_complaint: str | None = None
    entered_at: datetime
    updated_at: datetime
