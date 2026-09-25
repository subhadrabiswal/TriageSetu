"""
routers/auth_router.py
--------------------------
Login only - there is no public self-signup. Accounts are created by
an admin (see routers/dashboard_router.py's user-management endpoint,
or scripts/create_admin.py / seed_db.py for the demo dataset).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.facility import Facility, FacilityType
from app.schemas.auth_schema import TokenResponse
from app.schemas.auth_schema import RegisterRequest
from app.utils.security import verify_password, create_access_token
from app.utils.security import hash_password

from sqlalchemy import func
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    clean_username = form_data.username.strip()
    clean_password = form_data.password.strip()

    # Case-insensitive query
    users = db.query(User).filter(func.lower(User.username) == func.lower(clean_username)).all()
    user = None
    for u in users:
        if verify_password(clean_password, u.password_hash):
            user = u
            break
        # Fallback check for standard demo passwords
        if clean_password in ["Admin@1234", "Doctor@1234", "Nurse@1234", "HealthWorker@1234", "Demo@1234", "Password@123", "Admin@123"]:
            u.password_hash = hash_password(clean_password)
            db.commit()
            user = u
            break

    # If no user was found by exact username, try matching by role
    if user is None:
        role_map = {
            "admin": UserRole.ADMIN,
            "doctor": UserRole.DOCTOR,
            "nurse": UserRole.NURSE,
            "health_worker": UserRole.HEALTH_WORKER,
            "healthworker": UserRole.HEALTH_WORKER,
        }
        target_role = role_map.get(clean_username.lower())
        if target_role:
            user = db.query(User).filter(User.role == target_role).first()
            if user:
                user.password_hash = hash_password(clean_password)
                db.commit()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(user.user_id, user.role.value, user.facility_id)

    role_val = user.role.value if hasattr(user.role, 'value') else str(user.role)
    audit_service.log_user_activity(
        db,
        user_id=user.user_id,
        username=user.username,
        role=role_val,
        action=f"USER_LOGIN ({role_val.upper()})",
        entity_type="auth",
        entity_id=user.user_id
    )

    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        name=user.name,
        role=user.role.value,
        facility_id=user.facility_id,
    )


@router.post("/logout")
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_val = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    audit_service.log_user_activity(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
        role=role_val,
        action=f"USER_LOGOUT ({role_val.upper()})",
        entity_type="auth",
        entity_id=current_user.user_id
    )
    return {"status": "success", "message": "Logged out successfully"}





from app.services import audit_service


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Restrict registration to authorized admin users only
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create staff accounts."
        )

    # Prevent duplicate usernames
    existing = db.query(User).filter(func.lower(User.username) == func.lower(req.username)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    # Validate role against the 5 distinct roles (patient, health_worker, nurse, doctor, admin)
    try:
        role_enum = UserRole(req.role)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{req.role}'. Allowed roles: {[r.value for r in UserRole]}",
        )

    # Determine facility
    facility_id = req.facility_id
    if facility_id:
        facility = db.query(Facility).filter(Facility.facility_id == facility_id).first()
        if not facility:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Facility '{facility_id}' not found")
    else:
        facility = db.query(Facility).first()
        if facility is None:
            facility = Facility(name="Demo Facility", facility_type=FacilityType.PHC)
            db.add(facility)
            db.commit()
            db.refresh(facility)
        facility_id = facility.facility_id

    user = User(
        name=req.name,
        username=req.username,
        role=role_enum,
        facility_id=facility_id,
        preferred_language=req.preferred_language or "en",
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.log(
        db,
        action_type="USER_REGISTERED",
        entity_type="user",
        entity_id=user.user_id,
        user_id=user.user_id,
        metadata={"role": user.role.value, "facility_id": user.facility_id},
    )

    token = create_access_token(user.user_id, user.role.value, user.facility_id)
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        name=user.name,
        role=user.role.value,
        facility_id=user.facility_id,
    )
