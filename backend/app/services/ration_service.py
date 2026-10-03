from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import LocationStatus, StockLevel, UpdateType
from app.models.location import Location
from app.models.user import User
from app.schemas.details import RationStockUpdate
from app.services import audit_service
from app.services.location_service import touch
from app.utils.db import commit_or_raise


def update_stock(db: Session, location: Location, user: User, payload: RationStockUpdate) -> Location:
    """Update stock items, overall status and queue level in one transaction."""
    stock = location.ration_stock
    for item in ("rice", "wheat", "dal"):
        value = getattr(payload, item)
        if value is not None:
            audit_service.set_tracked(db, location, user, stock, item, value, UpdateType.STOCK, payload.note, f"stock.{item}")
    if payload.other_items is not None:
        audit_service.set_tracked(
            db, location, user, stock, "other_items", payload.other_items, UpdateType.STOCK, payload.note, "stock.other_items"
        )

    status = payload.status
    if status is None and {"rice", "wheat", "dal"} & payload.model_fields_set:
        # Derive overall status: all staples out -> OUT_OF_STOCK; recovery clears an OUT_OF_STOCK flag.
        staples = (stock.rice, stock.wheat, stock.dal)
        if all(level == StockLevel.OUT_OF_STOCK for level in staples):
            status = LocationStatus.OUT_OF_STOCK
        elif location.status == LocationStatus.OUT_OF_STOCK:
            status = LocationStatus.AVAILABLE
    if status is not None:
        audit_service.set_tracked(db, location, user, location, "status", status, UpdateType.STATUS, payload.note)
    if payload.queue_level is not None:
        audit_service.set_tracked(
            db, location, user, location, "queue_level", payload.queue_level, UpdateType.QUEUE, payload.note
        )
    touch(location)
    commit_or_raise(db)
    return location
