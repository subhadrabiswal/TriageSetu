from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentType


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    patient_id: str
    document_type: DocumentType
    file_reference: str
    ocr_extracted_text: str | None
    ocr_confidence_score: float | None
    uploaded_at: datetime
