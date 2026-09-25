"""
middleware/auth_middleware.py
--------------------------------
FastAPI dependencies that protect routes. Rather than a raw ASGI
middleware, these use FastAPI's Depends() system, which is the
idiomatic way to do per-route auth in FastAPI and keeps each
router's requirements visible in its own function signature.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    user = db.query(User).filter(User.user_id == payload.get("sub")).first()
    if user is None:
        raise credentials_error

    return user


def require_roles(*allowed_roles):
    """
    Usage: Depends(require_roles(UserRole.NURSE, UserRole.DOCTOR))
    Returns a dependency that 403s if the logged-in user's role isn't
    in the allowed set - keeps RBAC declarative right in the route
    signature instead of an if-check buried in the function body.
    """

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted to perform this action",
            )
        return current_user

    return checker
