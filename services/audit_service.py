"""
services/audit_service.py
-----------------------------
Writes one row per important action - AI-generated or human. This
is the audit trail required for accountability; nothing here is ever
updated or deleted, only appended.
"""

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log(db: Session, action_type: str, entity_type: str, entity_id: str,
        user_id: str | None = None, metadata: dict | None = None) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def log_user_activity(db: Session, user_id: str | None = None, username: str | None = None, role: str | None = None, action: str = "USER_ACTION", entity_type: str = "system", entity_id: str = "N/A", metadata: dict | None = None) -> AuditLog:
    """
    Central Audit Logger Function - captures every critical user activity
    (logins, logouts, patient additions, reviews, approvals, referrals across all roles).
    """
    meta = {
        "username": username,
        "role": role,
        **(metadata or {})
    }
    entry = AuditLog(
        user_id=user_id,
        action_type=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=meta,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

