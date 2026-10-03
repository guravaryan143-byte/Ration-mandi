from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user, require_owner_or_admin
from app.database import get_db
from app.models.enums import Category
from app.models.user import User
from app.routers.deps import category_filters, pagination
from app.schemas.common import ApiResponse, PageMeta, ok
from app.schemas.details import MedicineSearchResult, PharmacyInventoryUpdate
from app.schemas.location import LocationOut
from app.services import location_service as svc
from app.services import pharmacy_service
from app.utils.rate_limit import rate_limit
from app.websocket.manager import queue_broadcast

CATEGORY = Category.PHARMACY
router = APIRouter(prefix="/api/pharmacies", tags=["Pharmacies"])


@router.get("", response_model=ApiResponse[list[LocationOut]], dependencies=[Depends(rate_limit)])
def list_pharmacies(
    filters: svc.LocationFilters = Depends(category_filters),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    filters.category = CATEGORY
    rows, total = svc.search_locations(db, filters, *page)
    return ok([svc.to_out(loc, d) for loc, d in rows], PageMeta(total=total, limit=page[0], offset=page[1]))


# Declared before "/{location_id}" so "search-medicine" is not parsed as an id.
@router.get(
    "/search-medicine", response_model=ApiResponse[list[MedicineSearchResult]], dependencies=[Depends(rate_limit)]
)
def search_medicine(
    medicine: str = Query(..., min_length=2, max_length=200, description="Full or partial medicine name"),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius: float | None = Query(None, gt=0, le=200, description="km, default 10 when coordinates given"),
    available_only: bool = True,
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(get_db),
):
    """Pharmacies currently stocking a medicine, nearest first when coordinates are supplied."""
    results, total = pharmacy_service.search_medicine(
        db, medicine, latitude, longitude, radius, available_only, *page
    )
    return ok(results, PageMeta(total=total, limit=page[0], offset=page[1]))


@router.get("/{location_id}", response_model=ApiResponse[LocationOut])
def get_pharmacy(location_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return ok(svc.to_out(svc.get_visible_location(db, location_id, user, CATEGORY)))


@router.put("/{location_id}/inventory", response_model=ApiResponse[LocationOut])
def update_inventory(
    location_id: int,
    payload: PharmacyInventoryUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Upsert medicines (availability, optional quantity, prescription flag); inventory only."""
    location = svc.get_location_for_update(db, location_id, user, CATEGORY)
    pharmacy_service.update_inventory(db, location, user, payload)
    queue_broadcast(background_tasks, location)
    return ok(svc.to_out(location))
