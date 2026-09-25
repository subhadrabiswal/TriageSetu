from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.facility import FacilityType, DigitalMaturityLevel


class FacilityCreate(BaseModel):
    name: str
    facility_type: FacilityType
    state: str | None = None
    district: str | None = None
    digital_maturity_level: DigitalMaturityLevel = DigitalMaturityLevel.MEDIUM


class FacilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    facility_id: str
    name: str
    facility_type: FacilityType
    state: str | None
    district: str | None
    digital_maturity_level: DigitalMaturityLevel
    created_at: datetime
