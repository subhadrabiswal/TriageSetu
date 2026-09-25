"""
models/facility.py
-------------------
Represents a health facility: a government hospital, PHC, health camp,
clinic, industrial-estate health unit, or campus health center.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime

from app.database import Base


class FacilityType(str, enum.Enum):
    GOVT_HOSPITAL = "govt_hospital"
    PHC = "phc"
    HEALTH_CAMP = "health_camp"
    CLINIC = "clinic"
    INDUSTRIAL_HEALTH_UNIT = "industrial_health_unit"
    CAMPUS_HEALTH_CENTER = "campus_health_center"


class DigitalMaturityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Facility(Base):
    __tablename__ = "facilities"

    facility_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    facility_type = Column(Enum(FacilityType), nullable=False)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    digital_maturity_level = Column(Enum(DigitalMaturityLevel), default=DigitalMaturityLevel.MEDIUM)
    created_at = Column(DateTime, default=datetime.utcnow)
