from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import UpdateType
from app.models.location import Location
from app.models.user import User
from app.schemas.details import MuseumUpdate
from app.services import audit_service
from app.services.location_service import touch
from app.utils.db import commit_or_raise

_DETAIL_FIELDS = ("opening_hours", "historical_description", "guide_available", "guide_url", "guide_content_id")


def update_museum(db: Session, location: Location, user: User, payload: MuseumUpdate) -> Location:
    if payload.status is not None:
        audit_service.set_tracked(db, location, user, location, "status", payload.status, UpdateType.STATUS, payload.note)
    if payload.queue_level is not None:
        audit_service.set_tracked(
            db, location, user, location, "queue_level", payload.queue_level, UpdateType.QUEUE, payload.note, "crowd_level"
        )
    for field in _DETAIL_FIELDS:
        if field not in payload.model_fields_set:
            continue
        value = getattr(payload, field)
        if field == "guide_available" and value is None:
            continue  # null is not meaningful for a boolean flag
        audit_service.set_tracked(
            db, location, user, location.museum, field, value, UpdateType.MUSEUM, payload.note, f"museum.{field}"
        )
    touch(location)
    commit_or_raise(db)
    return location
