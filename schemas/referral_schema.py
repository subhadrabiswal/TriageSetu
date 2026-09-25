from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.referral import ReferralStatus


class ReferralCreate(BaseModel):
    patient_id: str
    triage_note_id: str
    referred_to_facility_name: str
    referral_reason: str | None = None


class ReferralOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    referral_id: str
    patient_id: str
    triage_note_id: str
    referred_to_facility_name: str
    referral_reason: str | None
    referral_note_text: str | None
    created_by: str
    status: ReferralStatus
    created_at: datetime
