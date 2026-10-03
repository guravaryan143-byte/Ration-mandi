from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.details import PharmacyMedicine
from app.models.enums import ApprovalStatus, Category, UpdateType
from app.models.location import Location
from app.models.user import User
from app.schemas.details import MedicineItem, MedicineSearchResult, PharmacyInventoryUpdate
from app.services import audit_service
from app.services.location_service import now, touch, validate_geo, LocationFilters
from app.utils.db import commit_or_raise
from app.utils.geo import bounding_box, haversine_km
from app.utils.text import normalize_name


def apply_medicine_items(db: Session, location: Location, user: User, items: list[MedicineItem], note: str | None = None) -> None:
    """Upsert medicines by normalised name; every change is audited."""
    existing = {m.name_key: m for m in location.medicines}
    stamp = now()
    for item in items:
        key = normalize_name(item.medicine_name)
        med = existing.get(key)
        if med is None:
            med = PharmacyMedicine(
                medicine_name=item.medicine_name,
                name_key=key,
                is_available=item.is_available,
                quantity=item.quantity,
                prescription_required=bool(item.prescription_required),
                last_stock_update=stamp,
            )
            location.medicines.append(med)
            existing[key] = med
            audit_service.record(
                db, location, user, UpdateType.PHARMACY_INVENTORY, f"medicine:{key}", None,
                {"is_available": med.is_available, "quantity": med.quantity}, note,
            )
            continue
        label = f"medicine:{key}"
        audit_service.set_tracked(db, location, user, med, "is_available", item.is_available, UpdateType.PHARMACY_INVENTORY, note, f"{label}.is_available")
        if "quantity" in item.model_fields_set:
            audit_service.set_tracked(db, location, user, med, "quantity", item.quantity, UpdateType.PHARMACY_INVENTORY, note, f"{label}.quantity")
        if item.prescription_required is not None:
            audit_service.set_tracked(db, location, user, med, "prescription_required", item.prescription_required, UpdateType.PHARMACY_INVENTORY, note, f"{label}.prescription_required")
        med.last_stock_update = stamp
    db.flush()


def update_inventory(db: Session, location: Location, user: User, payload: PharmacyInventoryUpdate) -> Location:
    apply_medicine_items(db, location, user, payload.items, payload.note)
    for name in payload.remove:
        key = normalize_name(name)
        med = next((m for m in location.medicines if m.name_key == key), None)
        if med is not None:
            audit_service.record(
                db, location, user, UpdateType.PHARMACY_INVENTORY, f"medicine:{key}",
                {"is_available": med.is_available, "quantity": med.quantity}, None, payload.note,
            )
            location.medicines.remove(med)
    if payload.status is not None:
        audit_service.set_tracked(db, location, user, location, "status", payload.status, UpdateType.STATUS, payload.note)
    if payload.queue_level is not None:
        audit_service.set_tracked(db, location, user, location, "queue_level", payload.queue_level, UpdateType.QUEUE, payload.note)
    touch(location)
    commit_or_raise(db)
    return location


def search_medicine(
    db: Session,
    medicine: str,
    latitude: float | None,
    longitude: float | None,
    radius_km: float | None,
    available_only: bool,
    limit: int,
    offset: int,
) -> tuple[list[MedicineSearchResult], int]:
    """Find approved pharmacies stocking a medicine, nearest first when coordinates are given."""
    filters = LocationFilters(latitude=latitude, longitude=longitude, radius_km=radius_km)
    validate_geo(filters)
    stmt = (
        select(PharmacyMedicine, Location)
        .join(Location, Location.id == PharmacyMedicine.location_id)
        .where(
            Location.category == Category.PHARMACY,
            Location.deleted_at.is_(None),
            Location.approval_status == ApprovalStatus.APPROVED,
            PharmacyMedicine.name_key.contains(normalize_name(medicine), autoescape=True),
        )
    )
    if available_only:
        stmt = stmt.where(PharmacyMedicine.is_available.is_(True))
    radius = radius_km if radius_km is not None else 10.0
    if latitude is not None and longitude is not None:
        min_lat, max_lat, min_lon, max_lon = bounding_box(latitude, longitude, radius)
        stmt = stmt.where(Location.latitude.between(min_lat, max_lat), Location.longitude.between(min_lon, max_lon))

    results: list[tuple[MedicineSearchResult, float]] = []
    for med, loc in db.execute(stmt).all():
        distance = None
        if latitude is not None and longitude is not None:
            distance = haversine_km(latitude, longitude, loc.latitude, loc.longitude)
            if distance > radius:
                continue
        results.append(
            (
                MedicineSearchResult(
                    location_id=loc.id,
                    pharmacy_name=loc.name,
                    address=loc.address,
                    phone=loc.phone,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    status=loc.status,
                    queue_level=loc.queue_level,
                    last_updated=loc.last_updated,
                    distance_km=round(distance, 2) if distance is not None else None,
                    medicine_name=med.medicine_name,
                    is_available=med.is_available,
                    quantity=med.quantity,
                    prescription_required=med.prescription_required,
                    last_stock_update=med.last_stock_update,
                ),
                distance if distance is not None else 0.0,
            )
        )
    if latitude is not None:
        results.sort(key=lambda r: (r[1], r[0].location_id))
    else:
        results.sort(key=lambda r: r[0].last_stock_update, reverse=True)
    page = [r[0] for r in results[offset : offset + limit]]
    return page, len(results)
