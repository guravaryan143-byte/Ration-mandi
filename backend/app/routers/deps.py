from __future__ import annotations

from fastapi import Query

from app.models.enums import LocationStatus, QueueLevel
from app.services.location_service import LocationFilters


def pagination(
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> tuple[int, int]:
    return limit, offset


def category_filters(
    status: LocationStatus | None = None,
    queue_level: QueueLevel | None = None,
    keyword: str | None = Query(None, min_length=1, max_length=100),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius: float | None = Query(None, gt=0, le=200, description="Radius in km (default 5 when coordinates given)"),
) -> LocationFilters:
    return LocationFilters(
        status=status, queue_level=queue_level, keyword=keyword,
        latitude=latitude, longitude=longitude, radius_km=radius,
    )
