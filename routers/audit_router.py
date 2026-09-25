"""
routers/audit_router.py
---------------------------
Admin-only read access to the audit trail.
"""

from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.middleware.auth_middleware import require_roles
from app.utils.rbac import ADMIN_ROLES

router = APIRouter(prefix="/audit-logs", tags=["audit"])


class AuditLogOut(BaseModel):
    log_id: str
    user_id: str | None
    user_name: str | None
    user_role: str | None
    action_type: str
    entity_type: str
    entity_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
    limit: int = 100,
):
    logs = (
        db.query(AuditLog, User.name, User.role)
        .outerjoin(User, AuditLog.user_id == User.user_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    result = []
    for log, name, role in logs:
        role_str = role.value if hasattr(role, 'value') else (str(role) if role else "Admin")
        result.append(
            AuditLogOut(
                log_id=log.log_id,
                user_id=log.user_id,
                user_name=name or "System Administrator",
                user_role=role_str.title(),
                action_type=log.action_type,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                timestamp=log.timestamp,
            )
        )
    return result
