from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_owner_or_admin
from app.database import get_db
from app.models.user import User
from app.routers.deps import pagination
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.location import (
    LocationCreate,
    LocationOut,
    LocationProfileUpdate,
    LocationUpdateOut,
    StatusUpdate,
)
from app.services import audit_service
from app.services import location_service as svc
from app.websocket.manager import queue_broadcast

router = APIRouter(prefix="/api/owner", tags=["Owner dashboard"], dependencies=[Depends(require_owner_or_admin)])


@router.get("/locations", response_model=ApiResponse[list[LocationOut]])
def my_locations(user: User = Depends(require_owner_or_admin), db: Session = Depends(get_db)):
    """Your locations (including PENDING/REJECTED) with current status, queue and details."""
    rows = svc.list_owner_locations(db, user)
    return ok([svc.to_out(r) for r in rows], PageMeta(total=len(rows), limit=len(rows), offset=0))


@router.post("/locations", response_model=ApiResponse[LocationOut], status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate, user: User = Depends(require_owner_or_admin), db: Session = Depends(get_db)
):
    """Owner-created locations start as PENDING until an admin approves them."""
    return ok(svc.to_out(svc.create_location(db, user, payload)))


@router.put("/locations/{location_id}", response_model=ApiResponse[LocationOut])
def update_location(
    location_id: int,
    payload: LocationProfileUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    location = svc.get_location_for_update(db, location_id, user)
    svc.update_profile(db, location, user, payload)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))


@router.delete("/locations/{location_id}", response_model=ApiResponse[dict])
def delete_location(location_id: int, user: User = Depends(require_owner_or_admin), db: Session = Depends(get_db)):
    """Soft delete: hidden everywhere but the audit history is kept."""
    location = svc.get_location_for_update(db, location_id, user)
    svc.soft_delete(db, location, user)
    return ok({"id": location_id, "deleted": True})


@router.get("/locations/{location_id}/updates", response_model=ApiResponse[list[LocationUpdateOut]])
def location_updates(
    location_id: int,
    page: tuple[int, int] = Depends(pagination),
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Audit trail (newest first): who changed what, when, old value -> new value."""
    svc.get_location_for_update(db, location_id, user)
    rows, total = audit_service.list_updates(db, location_id, *page)
    return ok([LocationUpdateOut.model_validate(r) for r in rows], PageMeta(total=total, limit=page[0], offset=page[1]))


@router.post("/locations/{location_id}/update-status", response_model=ApiResponse[LocationOut])
def update_status(
    location_id: int,
    payload: StatusUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Category-agnostic status/queue update (open/closed, busy, queue level...)."""
    location = svc.get_location_for_update(db, location_id, user)
    svc.update_status(db, location, user, payload.status, payload.queue_level, payload.note)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))
