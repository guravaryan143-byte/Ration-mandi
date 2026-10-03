from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut
from app.schemas.common import ApiResponse, ok
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse[UserOut], status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Create a CITIZEN or OWNER (shopkeeper) account. Admins are created by an operator."""
    return ok(UserOut.model_validate(auth_service.register_user(db, payload)))


@router.post("/login", response_model=ApiResponse[TokenOut])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return ok(auth_service.login(db, payload))


@router.get("/me", response_model=ApiResponse[UserOut])
def me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))
