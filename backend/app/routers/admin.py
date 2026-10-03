from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.enums import ApprovalStatus, Category, UserRole
from app.models.user import User
from app.routers.deps import pagination
from app.schemas.admin import RejectRequest, StatsOut, UserActiveUpdate
from app.schemas.auth import UserOut
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.location import LocationOut
from app.services import admin_service
from app.services import location_service as svc

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=ApiResponse[list[UserOut]])
def list_users(
    role: UserRole | None = None, page: tuple[int, int] = Depends(pagination), db: Session = Depends(get_db)
):
    users, total = admin_service.list_users(db, role, *page)
    return ok([UserOut.model_validate(u) for u in users], PageMeta(total=total, limit=page[0], offset=page[1]))


@router.put("/users/{user_id}/active", response_model=ApiResponse[UserOut])
def set_user_active(
    user_id: int, payload: UserActiveUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Enable/disable an account (disabled users cannot log in or use existing tokens)."""
    return ok(UserOut.model_validate(admin_service.set_user_active(db, admin, user_id, payload.is_active)))


@router.get("/locations", response_model=ApiResponse[list[LocationOut]])
def list_locations(
    approval_status: ApprovalStatus | None = None,
    category: Category | None = None,
    include_deleted: bool = False,
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    rows, total = admin_service.list_locations(db, approval_status, category, include_deleted, *page)
    return ok([svc.to_out(r) for r in rows], PageMeta(total=total, limit=page[0], offset=page[1]))


@router.put("/locations/{location_id}/approve", response_model=ApiResponse[LocationOut])
def approve(location_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return ok(svc.to_out(admin_service.moderate(db, admin, location_id, approve=True)))


@router.put("/locations/{location_id}/reject", response_model=ApiResponse[LocationOut])
def reject(
    location_id: int,
    payload: RejectRequest | None = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reject (hides from the public). Use for fraudulent or inactive listings."""
    reason = payload.reason if payload else None
    return ok(svc.to_out(admin_service.moderate(db, admin, location_id, approve=False, reason=reason)))


@router.delete("/locations/{location_id}", response_model=ApiResponse[dict])
def delete_location(location_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    admin_service.delete_location(db, admin, location_id)
    return ok({"id": location_id, "deleted": True})


@router.get("/stats", response_model=ApiResponse[StatsOut])
def stats(db: Session = Depends(get_db)):
    return ok(admin_service.statistics(db))
