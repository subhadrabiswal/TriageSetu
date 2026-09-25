from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role: UserRole
    facility_id: str
    preferred_language: str = "en"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    name: str
    username: str
    role: UserRole
    facility_id: str
    preferred_language: str
    created_at: datetime
