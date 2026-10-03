"""Audit trail helpers: every real change is recorded with who/when/old/new."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import LocationUpdate
from app.models.enums import UpdateType
from app.models.location import Location
from app.models.user import User


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, dict | list):
        return json.dumps(value, sort_keys=True, default=lambda v: v.value if isinstance(v, Enum) else str(v))
    return str(value)


def record(
    db: Session,
    location: Location,
    user: User,
    update_type: UpdateType,
    field_name: str,
    previous: Any,
    new: Any,
    note: str | None = None,
) -> None:
    db.add(
        LocationUpdate(
            location_id=location.id,
            updated_by=user.id,
            update_type=update_type,
            field_name=field_name,
            previous_value=_to_str(previous),
            new_value=_to_str(new),
            note=note,
            created_at=datetime.now(UTC),
        )
    )


def set_tracked(
    db: Session,
    location: Location,
    user: User,
    target: Any,
    attr: str,
    new: Any,
    update_type: UpdateType,
    note: str | None = None,
    label: str | None = None,
) -> bool:
    """Set target.attr = new and audit it if the value actually changed."""
    old = getattr(target, attr)
    if old == new:
        return False
    setattr(target, attr, new)
    record(db, location, user, update_type, label or attr, old, new, note)
    return True


def list_updates(db: Session, location_id: int, limit: int, offset: int) -> tuple[list[LocationUpdate], int]:
    total = db.scalar(select(func.count(LocationUpdate.id)).where(LocationUpdate.location_id == location_id)) or 0
    rows = db.scalars(
        select(LocationUpdate)
        .where(LocationUpdate.location_id == location_id)
        .order_by(LocationUpdate.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), total
