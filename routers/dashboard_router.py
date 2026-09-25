from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.patient import Patient
from app.models.triage_note import TriageNote, RiskCategory
from app.models.facility_queue import FacilityQueue, QueueStatus
from app.models.user import User, UserRole
from app.middleware.auth_middleware import get_current_user
from app.utils.security import hash_password
from app.services import audit_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardSummary(BaseModel):
    patients_total: int
    waiting_in_queue: int
    red_count: int
    yellow_count: int
    green_count: int
    staff_total: int


class StaffOut(BaseModel):
    user_id: str
    name: str
    username: str
    role: str
    status: str
    staff_code: str

    class Config:
        from_attributes = True


class CreateStaffRequest(BaseModel):
    name: str
    username: str
    password: str
    role: str


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    facility_id = current_user.facility_id

    patients_total = db.query(func.count(Patient.patient_id)).filter(
        Patient.facility_id == facility_id
    ).scalar()

    waiting_in_queue = db.query(func.count(FacilityQueue.queue_id)).filter(
        FacilityQueue.facility_id == facility_id,
        FacilityQueue.status == QueueStatus.WAITING,
    ).scalar()

    staff_total = db.query(func.count(User.user_id)).scalar()

    def count_by_risk(category: RiskCategory) -> int:
        return (
            db.query(func.count(TriageNote.triage_note_id))
            .join(Patient, Patient.patient_id == TriageNote.patient_id)
            .filter(Patient.facility_id == facility_id, TriageNote.risk_category == category)
            .scalar()
        )

    return DashboardSummary(
        patients_total=patients_total or 0,
        waiting_in_queue=waiting_in_queue or 0,
        red_count=count_by_risk(RiskCategory.RED) or 0,
        yellow_count=count_by_risk(RiskCategory.YELLOW) or 0,
        green_count=count_by_risk(RiskCategory.GREEN) or 0,
        staff_total=staff_total or 0,
    )


@router.get("/staff", response_model=list[StaffOut])
def get_staff_members(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).order_by(User.created_at.asc()).all()
    result = []
    for idx, u in enumerate(users, start=1):
        result.append(StaffOut(
            user_id=u.user_id,
            name=u.name,
            username=u.username,
            role=u.role.value if hasattr(u.role, 'value') else str(u.role),
            status="Active",
            staff_code=f"STF-{idx:03d}"
        ))
    return result


@router.post("/staff", response_model=StaffOut)
def create_staff_member(req: CreateStaffRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can add new staff."
        )

    existing = db.query(User).filter(func.lower(User.username) == func.lower(req.username)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    try:
        role_enum = UserRole(req.role.lower())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {req.role}")

    user = User(
        name=req.name,
        username=req.username,
        role=role_enum,
        facility_id=current_user.facility_id,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.log(
        db,
        action_type="STAFF_ADDED",
        entity_type="user",
        entity_id=user.user_id,
        user_id=current_user.user_id,
        metadata={"name": user.name, "role": user.role.value},
    )

    total_count = db.query(func.count(User.user_id)).scalar() or 1
    return StaffOut(
        user_id=user.user_id,
        name=user.name,
        username=user.username,
        role=user.role.value,
        status="Active",
        staff_code=f"STF-{total_count:03d}"
    )
