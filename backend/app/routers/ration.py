from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user, require_owner_or_admin
from app.database import get_db
from app.models.enums import Category
from app.models.user import User
from app.routers.deps import category_filters, pagination
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.details import RationStockUpdate
from app.schemas.location import LocationOut, StatusUpdate
from app.services import location_service as svc
from app.services import ration_service
from app.utils.rate_limit import rate_limit
from app.websocket.manager import queue_broadcast

CATEGORY = Category.RATION_SHOP
router = APIRouter(prefix="/api/ration-shops", tags=["Ration shops"])


@router.get("", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def list_ration_shops(
    filters: svc.LocationFilters = Depends(category_filters),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    filters.category = CATEGORY
    rows, total = svc.search_locations(db, filters, *page)
    return ok([svc.to_out(loc, d) for loc, d in rows], PageMeta(total=total, limit=page[0], offset=page[1]))


@router.get("/{location_id}", response_model=ApiResponse[LocationOut])
def get_ration_shop(location_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return ok(svc.to_out(svc.get_visible_location(db, location_id, user, CATEGORY)))


@router.put("/{location_id}/status", response_model=ApiResponse[LocationOut])
def update_status(
    location_id: int,
    payload: StatusUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Update overall stock status and/or queue level."""
    location = svc.get_location_for_update(db, location_id, user, CATEGORY)
    svc.update_status(db, location, user, payload.status, payload.queue_level, payload.note)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))


@router.put("/{location_id}/stock", response_model=ApiResponse[LocationOut])
def update_stock(
    location_id: int,
    payload: RationStockUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Rice/wheat/dal/other items + overall status + queue level in a single request."""
    location = svc.get_location_for_update(db, location_id, user, CATEGORY)
    ration_service.update_stock(db, location, user, payload)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))
