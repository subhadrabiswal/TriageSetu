"""
services/seed_service.py
--------------------------
Automatically seeds default demo accounts for all roles (Admin, Doctor, Nurse,
Health Worker) on database startup, so login authentication always works out of the box.
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.facility import Facility, FacilityType, DigitalMaturityLevel
from app.utils.security import hash_password

DEFAULT_USERS = [
    # (username, name, role, primary_password)
    ("Admin", "Facility Admin", UserRole.ADMIN, "Admin@1234"),
    ("admin", "Facility Admin", UserRole.ADMIN, "Admin@1234"),
    ("doctor", "Dr. Meera Nayak", UserRole.DOCTOR, "Doctor@1234"),
    ("drmeera", "Dr. Meera Nayak", UserRole.DOCTOR, "Demo@1234"),
    ("nurse", "Priya Sahoo", UserRole.NURSE, "Nurse@1234"),
    ("nursepriya", "Priya Sahoo", UserRole.NURSE, "Demo@1234"),
    ("health_worker", "Ravi Behera", UserRole.HEALTH_WORKER, "HealthWorker@1234"),
    ("workerravi", "Ravi Behera", UserRole.HEALTH_WORKER, "Demo@1234"),
]


def seed_default_users():
    db: Session = SessionLocal()
    try:
        facility = db.query(Facility).first()
        if facility is None:
            facility = Facility(
                name="Dhenkanal Government PHC",
                facility_type=FacilityType.PHC,
                state="Odisha",
                district="Dhenkanal",
                digital_maturity_level=DigitalMaturityLevel.MEDIUM,
            )
            db.add(facility)
            db.commit()
            db.refresh(facility)

        for username, name, role, pass_str in DEFAULT_USERS:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                u = User(
                    name=name,
                    username=username,
                    role=role,
                    facility_id=facility.facility_id,
                    password_hash=hash_password(pass_str),
                )
                db.add(u)
                db.commit()
    except Exception as e:
        print(f"Error seeding default users: {e}")
    finally:
        db.close()
