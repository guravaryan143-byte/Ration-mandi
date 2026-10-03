from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.utils.errors import AppError, forbidden

bearer_scheme = HTTPBearer(auto_error=False, description="Paste the access_token from POST /api/auth/login")


def _user_from_token(token: str, db: Session) -> User:
    payload = decode_access_token(token)
    try:
        user = db.get(User, int(payload["sub"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise AppError(401, "INVALID_TOKEN", "Invalid token", {"WWW-Authenticate": "Bearer"}) from exc
    if user is None or not user.is_active:
        raise AppError(401, "INVALID_TOKEN", "User not found or disabled", {"WWW-Authenticate": "Bearer"})
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError(401, "NOT_AUTHENTICATED", "Authentication required", {"WWW-Authenticate": "Bearer"})
    return _user_from_token(credentials.credentials, db)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """For public endpoints: owners/admins get extra visibility, bad tokens are treated as anonymous."""
    if credentials is None:
        return None
    try:
        return _user_from_token(credentials.credentials, db)
    except AppError:
        return None


def require_roles(*roles: UserRole) -> Callable[..., User]:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise forbidden("Your role is not allowed to access this endpoint")
        return user

    return checker


require_owner_or_admin = require_roles(UserRole.OWNER, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)
