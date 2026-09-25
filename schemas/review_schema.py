from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.reviewer_action import ReviewerActionType


from app.models.triage_note import RiskCategory


class ReviewActionRequest(BaseModel):
    action_type: ReviewerActionType
    comments: str | None = None
    edited_summary_text: str | None = None
    edited_risk_category: RiskCategory | None = None


class ReviewerActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    triage_note_id: str
    reviewer_id: str
    action_type: ReviewerActionType
    comments: str | None
    edited_summary_text: str | None
    action_timestamp: datetime
