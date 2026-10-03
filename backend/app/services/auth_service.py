from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut
from app.utils.db import commit_or_raise
from app.utils.errors import AppError

# Pre-computed hash so login time doesn't reveal whether an email exists.
_DUMMY_HASH = hash_password("not-a-real-password-1")


def register_user(db: Session, payload: RegisterRequest) -> User:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise AppError(409, "EMAIL_ALREADY_REGISTERED", "An account with this email already exists")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    commit_or_raise(db)
    return user


def login(db: Session, payload: LoginRequest) -> TokenOut:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    valid = verify_password(payload.password, user.hashed_password if user else _DUMMY_HASH)
    if user is None or not valid:
        raise AppError(401, "INVALID_CREDENTIALS", "Incorrect email or password", {"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "This account has been disabled")
    token, expires_in = create_access_token(user)
    return TokenOut(access_token=token, expires_in=expires_in, user=UserOut.model_validate(user))
