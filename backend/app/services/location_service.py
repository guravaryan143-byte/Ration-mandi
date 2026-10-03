"""Location queries, creation, ownership checks and generic status updates."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.details import EVStationDetails, MuseumDetails, PharmacyMedicine, RationStock
from app.models.enums import ApprovalStatus, Category, LocationStatus, QueueLevel, UpdateType, UserRole
from app.models.location import Location
from app.models.user import User
from app.schemas.location import LocationCreate, LocationOut, LocationProfileUpdate
from app.services import audit_service
from app.utils.db import commit_or_raise
from app.utils.errors import AppError, forbidden, not_found
from app.utils.geo import bounding_box, haversine_km
from app.utils.text import normalize_name

MAX_GEO_CANDIDATES = 5000

_LOAD = (
    selectinload(Location.ration_stock),
    selectinload(Location.museum),
    selectinload(Location.ev_station),
    selectinload(Location.medicines),
)


@dataclass
class LocationFilters:
    category: Category | None = None
    status: LocationStatus | None = None
    queue_level: QueueLevel | None = None
    keyword: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = None


def now() -> datetime:
    return datetime.now(UTC)


def to_out(location: Location, distance_km: float | None = None) -> LocationOut:
    out = LocationOut.model_validate(location)
    out.distance_km = round(distance_km, 2) if distance_km is not None else None
    return out


# ------------------------------------------------------------------ queries
def validate_geo(filters: LocationFilters, require: bool = False) -> None:
    has_lat, has_lon = filters.latitude is not None, filters.longitude is not None
    if has_lat != has_lon or (require and not has_lat):
        raise AppError(422, "INVALID_GEO_PARAMS", "latitude and longitude must be provided together")
    if filters.radius_km is not None and not has_lat:
        raise AppError(422, "INVALID_GEO_PARAMS", "radius requires latitude and longitude")


def search_locations(
    db: Session, filters: LocationFilters, limit: int, offset: int
) -> tuple[list[tuple[Location, float | None]], int]:
    """Public search: approved, non-deleted locations. Returns [(location, distance_km)], total."""
    validate_geo(filters)
    stmt = select(Location).where(
        Location.deleted_at.is_(None), Location.approval_status == ApprovalStatus.APPROVED
    )
    if filters.category:
        stmt = stmt.where(Location.category == filters.category)
    if filters.status:
        stmt = stmt.where(Location.status == filters.status)
    if filters.queue_level:
        stmt = stmt.where(Location.queue_level == filters.queue_level)
    if filters.keyword:
        kw = filters.keyword.strip()
        stmt = stmt.where(
            or_(
                Location.name.icontains(kw, autoescape=True),
                Location.address.icontains(kw, autoescape=True),
                Location.description.icontains(kw, autoescape=True),
                exists().where(
                    PharmacyMedicine.location_id == Location.id,
                    PharmacyMedicine.name_key.contains(normalize_name(kw), autoescape=True),
                ),
            )
        )

    if filters.latitude is None:
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.scalars(stmt.options(*_LOAD).order_by(Location.name, Location.id).limit(limit).offset(offset)).all()
        return [(r, None) for r in rows], total

    radius = filters.radius_km if filters.radius_km is not None else 5.0
    min_lat, max_lat, min_lon, max_lon = bounding_box(filters.latitude, filters.longitude, radius)
    stmt = stmt.where(
        Location.latitude.between(min_lat, max_lat), Location.longitude.between(min_lon, max_lon)
    )
    candidates = db.scalars(stmt.options(*_LOAD).limit(MAX_GEO_CANDIDATES)).all()
    scored = [
        (loc, haversine_km(filters.latitude, filters.longitude, loc.latitude, loc.longitude)) for loc in candidates
    ]
    within = sorted((x for x in scored if x[1] <= radius), key=lambda x: (x[1], x[0].id))
    return within[offset : offset + limit], len(within)


def can_view_unapproved(user: User | None, location: Location) -> bool:
    return user is not None and (user.role == UserRole.ADMIN or location.owner_id == user.id)


def get_visible_location(
    db: Session, location_id: int, user: User | None = None, category: Category | None = None
) -> Location:
    """Public read: approved locations for everyone; owner/admin can also see their pending ones."""
    location = db.scalar(
        select(Location).options(*_LOAD).where(Location.id == location_id, Location.deleted_at.is_(None))
    )
    if location is None or (category and location.category != category):
        raise not_found()
    if location.approval_status != ApprovalStatus.APPROVED and not can_view_unapproved(user, location):
        raise not_found()
    return location


def get_location_for_update(
    db: Session, location_id: int, user: User, category: Category | None = None
) -> Location:
    """Write access: owner of the location, or admin. Others get 403 (404 if it doesn't exist)."""
    location = db.scalar(
        select(Location).options(*_LOAD).where(Location.id == location_id, Location.deleted_at.is_(None))
    )
    if location is None or (category and location.category != category):
        raise not_found()
    if user.role != UserRole.ADMIN and location.owner_id != user.id:
        if location.approval_status != ApprovalStatus.APPROVED:
            raise not_found()  # don't reveal other people's pending locations
        raise forbidden("You can only modify locations you own")
    return location


def list_owner_locations(db: Session, user: User) -> list[Location]:
    return list(
        db.scalars(
            select(Location)
            .options(*_LOAD)
            .where(Location.owner_id == user.id, Location.deleted_at.is_(None))
            .order_by(Location.id)
        ).all()
    )


# ------------------------------------------------------------------ writes
def touch(location: Location) -> None:
    location.last_updated = now()


def create_location(db: Session, user: User, payload: LocationCreate) -> Location:
    from app.services.pharmacy_service import apply_medicine_items  # local import avoids a cycle

    location = Location(
        name=payload.name,
        category=payload.category,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        phone=payload.phone,
        description=payload.description,
        status=payload.status,
        queue_level=payload.queue_level,
        owner_id=user.id,
        # Admin-created locations are trusted; owner-created ones wait for approval.
        approval_status=ApprovalStatus.APPROVED if user.role == UserRole.ADMIN else ApprovalStatus.PENDING,
        last_updated=now(),
    )
    if payload.category == Category.RATION_SHOP:
        stock_values = payload.ration_stock.model_dump(exclude_none=True) if payload.ration_stock else {}
        location.ration_stock = RationStock(
            **{k: v for k, v in stock_values.items() if k in {"rice", "wheat", "dal", "other_items"}}
        )
    elif payload.category == Category.MUSEUM_MONUMENT:
        location.museum = MuseumDetails(**(payload.museum.model_dump() if payload.museum else {}))
    elif payload.category == Category.EV_CHARGING:
        location.ev_station = EVStationDetails(**payload.ev_station.model_dump())  # type: ignore[union-attr]
    db.add(location)
    db.flush()
    audit_service.record(
        db, location, user, UpdateType.CREATED, "location", None, f"{payload.category.value}: {payload.name}"
    )
    if payload.category == Category.PHARMACY and payload.medicines:
        apply_medicine_items(db, location, user, payload.medicines)
    commit_or_raise(db)
    return location


def update_profile(db: Session, location: Location, user: User, payload: LocationProfileUpdate) -> Location:
    for field in payload.model_fields_set:
        value = getattr(payload, field)
        if value is None and field not in {"phone", "description"}:
            continue
        audit_service.set_tracked(db, location, user, location, field, value, UpdateType.PROFILE)
    touch(location)
    commit_or_raise(db)
    return location


def update_status(
    db: Session,
    location: Location,
    user: User,
    status: LocationStatus | None,
    queue_level: QueueLevel | None,
    note: str | None = None,
) -> Location:
    if status is not None:
        audit_service.set_tracked(db, location, user, location, "status", status, UpdateType.STATUS, note)
    if queue_level is not None:
        audit_service.set_tracked(db, location, user, location, "queue_level", queue_level, UpdateType.QUEUE, note)
    touch(location)
    commit_or_raise(db)
    return location


def soft_delete(db: Session, location: Location, user: User) -> None:
    location.deleted_at = now()
    audit_service.record(db, location, user, UpdateType.DELETED, "deleted_at", None, location.deleted_at)
    commit_or_raise(db)
