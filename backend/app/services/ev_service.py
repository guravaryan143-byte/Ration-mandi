from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import LocationStatus, UpdateType
from app.models.location import Location
from app.models.user import User
from app.schemas.details import EVAvailabilityUpdate
from app.services import audit_service
from app.services.location_service import touch
from app.utils.db import commit_or_raise
from app.utils.errors import AppError


def update_availability(db: Session, location: Location, user: User, payload: EVAvailabilityUpdate) -> Location:
    ev = location.ev_station
    total = payload.total_plugs if payload.total_plugs is not None else ev.total_plugs
    occupied = payload.occupied_plugs if payload.occupied_plugs is not None else ev.occupied_plugs
    if occupied > total:
        raise AppError(
            422,
            "INVALID_PLUG_COUNT",
            f"occupied_plugs ({occupied}) cannot exceed total_plugs ({total})",
        )

    note = payload.note
    for field, label in (
        ("total_plugs", "ev.total_plugs"),
        ("occupied_plugs", "ev.occupied_plugs"),
        ("charging_type", "ev.charging_type"),
        ("estimated_wait_minutes", "ev.estimated_wait_minutes"),
    ):
        value = getattr(payload, field)
        if value is not None:
            audit_service.set_tracked(db, location, user, ev, field, value, UpdateType.EV_AVAILABILITY, note, label)

    status = payload.status
    if status is None and location.status in {LocationStatus.AVAILABLE, LocationStatus.BUSY}:
        # Derive: no free plug -> BUSY, free plug again -> AVAILABLE. Manual states are never overridden.
        status = LocationStatus.BUSY if total - occupied == 0 else LocationStatus.AVAILABLE
    if status is not None:
        audit_service.set_tracked(db, location, user, location, "status", status, UpdateType.STATUS, note)
    if payload.queue_level is not None:
        audit_service.set_tracked(db, location, user, location, "queue_level", payload.queue_level, UpdateType.QUEUE, note)
    touch(location)
    commit_or_raise(db)
    return location
