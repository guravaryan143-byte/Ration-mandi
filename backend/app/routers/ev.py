from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user, require_owner_or_admin
from app.database import get_db
from app.models.enums import Category
from app.models.user import User
from app.routers.deps import category_filters, pagination
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.details import EVAvailabilityUpdate
from app.schemas.location import LocationOut
from app.services import ev_service
from app.services import location_service as svc
from app.utils.rate_limit import rate_limit
from app.websocket.manager import queue_broadcast

CATEGORY = Category.EV_CHARGING
router = APIRouter(prefix="/api/ev-stations", tags=["EV charging"])


@router.get("", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def list_ev_stations(
    filters: svc.LocationFilters = Depends(category_filters),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    filters.category = CATEGORY
    rows, total = svc.search_locations(db, filters, *page)
    return ok([svc.to_out(loc, d) for loc, d in rows], PageMeta(total=total, limit=page[0], offset=page[1]))


@router.get("/{location_id}", response_model=ApiResponse[LocationOut])
def get_ev_station(location_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return ok(svc.to_out(svc.get_visible_location(db, location_id, user, CATEGORY)))


@router.put("/{location_id}/availability", response_model=ApiResponse[LocationOut])
def update_availability(
    location_id: int,
    payload: EVAvailabilityUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Plugs, wait time, queue and status. available_plugs = total_plugs - occupied_plugs."""
    location = svc.get_location_for_update(db, location_id, user, CATEGORY)
    ev_service.update_availability(db, location, user, payload)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))
