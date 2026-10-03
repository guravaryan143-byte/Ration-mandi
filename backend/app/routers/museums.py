from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user, require_owner_or_admin
from app.database import get_db
from app.models.enums import Category
from app.models.user import User
from app.routers.deps import category_filters, pagination
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.details import GuideOut, MuseumUpdate
from app.schemas.location import LocationOut
from app.services import location_service as svc
from app.services import museum_service
from app.utils.rate_limit import rate_limit
from app.websocket.manager import queue_broadcast

CATEGORY = Category.MUSEUM_MONUMENT
router = APIRouter(prefix="/api/museums", tags=["Museums & monuments"])


@router.get("", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def list_museums(
    filters: svc.LocationFilters = Depends(category_filters),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    filters.category = CATEGORY
    rows, total = svc.search_locations(db, filters, *page)
    return ok([svc.to_out(loc, d) for loc, d in rows], PageMeta(total=total, limit=page[0], offset=page[1]))


@router.get("/{location_id}", response_model=ApiResponse[LocationOut])
def get_museum(location_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return ok(svc.to_out(svc.get_visible_location(db, location_id, user, CATEGORY)))


@router.get("/{location_id}/guide", response_model=ApiResponse[GuideOut])
def get_guide(location_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    """Digital/audio guide availability plus the URL or content id to load it."""
    loc = svc.get_visible_location(db, location_id, user, CATEGORY)
    m = loc.museum
    return ok(
        GuideOut(
            location_id=loc.id, name=loc.name, guide_available=m.guide_available, guide_url=m.guide_url,
            guide_content_id=m.guide_content_id, opening_hours=m.opening_hours,
            historical_description=m.historical_description,
        )
    )


@router.put("/{location_id}/status", response_model=ApiResponse[LocationOut])
def update_museum_status(
    location_id: int,
    payload: MuseumUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Open/closed status, crowd level, opening hours, description and guide link."""
    location = svc.get_location_for_update(db, location_id, user, CATEGORY)
    museum_service.update_museum(db, location, user, payload)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))
