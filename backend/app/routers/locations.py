from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.enums import Category, LocationStatus, QueueLevel
from app.models.user import User
from app.routers.deps import pagination
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.location import LocationOut
from app.services import location_service as svc
from app.utils.rate_limit import rate_limit

router = APIRouter(prefix="/api/locations", tags=["Public locations"])


def _page(rows, total: int, limit: int, offset: int):  # noqa: ANN001
    return ok([svc.to_out(loc, dist) for loc, dist in rows], PageMeta(total=total, limit=limit, offset=offset))


@router.get("", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def list_locations(
    category: Category | None = None,
    status: LocationStatus | None = None,
    queue_level: QueueLevel | None = None,
    keyword: str | None = Query(None, min_length=1, max_length=100),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius: float | None = Query(None, gt=0, le=200, description="km; needs latitude+longitude"),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    """Filter by category, status, queue level, keyword and/or distance."""
    filters = svc.LocationFilters(category, status, queue_level, keyword, latitude, longitude, radius)
    rows, total = svc.search_locations(db, filters, *page)
    return _page(rows, total, *page)


@router.get("/nearby", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(5.0, gt=0, le=200, description="km"),
    category: Category | None = None,
    status: LocationStatus | None = None,
    queue_level: QueueLevel | None = None,
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    """Locations within `radius` km, nearest first, each with distance_km."""
    filters = svc.LocationFilters(category, status, queue_level, None, latitude, longitude, radius)
    rows, total = svc.search_locations(db, filters, *page)
    return _page(rows, total, *page)


@router.get("/search", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def search(
    keyword: str = Query(..., min_length=1, max_length=100, description="Matches name, address, description, medicines"),
    category: Category | None = None,
    status: LocationStatus | None = None,
    queue_level: QueueLevel | None = None,
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius: float | None = Query(None, gt=0, le=200),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    filters = svc.LocationFilters(category, status, queue_level, keyword, latitude, longitude, radius)
    rows, total = svc.search_locations(db, filters, *page)
    return _page(rows, total, *page)


@router.get("/{location_id}", response_model=ApiResponse[LocationOut])
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return ok(svc.to_out(svc.get_visible_location(db, location_id, user)))
