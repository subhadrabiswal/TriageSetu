"""
services/queue_service.py
-----------------------------
Manages the facility's prioritized waiting list. priority_rank is
derived straight from the triage note's risk_category so the
sickest-sounding patients surface first, without any separate
scoring model to maintain.
"""

from sqlalchemy.orm import Session

from app.models.facility_queue import FacilityQueue, QueueStatus
from app.models.triage_note import RiskCategory

_RANK_BY_RISK = {RiskCategory.RED: 1, RiskCategory.YELLOW: 2, RiskCategory.GREEN: 3}


def add_to_queue(db: Session, patient_id: str, facility_id: str,
                  risk_category: RiskCategory) -> FacilityQueue:
    entry = FacilityQueue(
        patient_id=patient_id,
        facility_id=facility_id,
        priority_rank=_RANK_BY_RISK.get(risk_category, 3),
        status=QueueStatus.WAITING,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_queue(db: Session, facility_id: str) -> list[FacilityQueue]:
    return (
        db.query(FacilityQueue)
        .filter(FacilityQueue.facility_id == facility_id)
        .filter(FacilityQueue.status != QueueStatus.COMPLETED)
        .order_by(FacilityQueue.priority_rank.asc(), FacilityQueue.entered_at.asc())
        .all()
    )


def update_status(db: Session, queue_id: str, status: QueueStatus) -> FacilityQueue | None:
    entry = db.query(FacilityQueue).filter(FacilityQueue.queue_id == queue_id).first()
    if entry:
        entry.status = status
        db.commit()
        db.refresh(entry)
    return entry
