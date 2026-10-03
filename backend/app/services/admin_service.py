from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import LocationUpdate
from app.models.enums import ApprovalStatus, Category, UpdateType, UserRole
from app.models.location import Location
from app.models.user import User
from app.schemas.admin import StatsOut
from app.services import audit_service
from app.services.location_service import _LOAD, now, soft_delete
from app.utils.db import commit_or_raise
from app.utils.errors import AppError, not_found


def list_users(db: Session, role: UserRole | None, limit: int, offset: int) -> tuple[list[User], int]:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return list(db.scalars(stmt.order_by(User.id).limit(limit).offset(offset)).all()), total


def set_user_active(db: Session, admin: User, user_id: int, is_active: bool) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "User not found")
    if user.id == admin.id and not is_active:
        raise AppError(400, "CANNOT_DISABLE_SELF", "Admins cannot disable their own account")
    user.is_active = is_active
    commit_or_raise(db)
    return user


def list_locations(
    db: Session,
    approval: ApprovalStatus | None,
    category: Category | None,
    include_deleted: bool,
    limit: int,
    offset: int,
) -> tuple[list[Location], int]:
    stmt = select(Location)
    if approval:
        stmt = stmt.where(Location.approval_status == approval)
    if category:
        stmt = stmt.where(Location.category == category)
    if not include_deleted:
        stmt = stmt.where(Location.deleted_at.is_(None))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.options(*_LOAD).order_by(Location.id).limit(limit).offset(offset)).all()
    return list(rows), total


def get_any_location(db: Session, location_id: int) -> Location:
    location = db.scalar(select(Location).options(*_LOAD).where(Location.id == location_id, Location.deleted_at.is_(None)))
    if location is None:
        raise not_found()
    return location


def moderate(db: Session, admin: User, location_id: int, approve: bool, reason: str | None = None) -> Location:
    location = get_any_location(db, location_id)
    new_state = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
    audit_service.set_tracked(db, location, admin, location, "approval_status", new_state, UpdateType.MODERATION, reason)
    location.rejection_reason = None if approve else reason
    location.last_updated = now()
    commit_or_raise(db)
    return location


def delete_location(db: Session, admin: User, location_id: int) -> None:
    soft_delete(db, get_any_location(db, location_id), admin)


def statistics(db: Session) -> StatsOut:
    def grouped(column) -> dict[str, int]:  # noqa: ANN001
        rows = db.execute(select(column, func.count()).group_by(column)).all()
        return {(k.value if hasattr(k, "value") else str(k)): v for k, v in rows}

    live = Location.deleted_at.is_(None)
    by_cat = db.execute(select(Location.category, func.count()).where(live).group_by(Location.category)).all()
    by_approval = db.execute(select(Location.approval_status, func.count()).where(live).group_by(Location.approval_status)).all()
    by_status = db.execute(select(Location.status, func.count()).where(live).group_by(Location.status)).all()
    users_by_role = grouped(User.role)
    return StatsOut(
        users_total=sum(users_by_role.values()),
        users_by_role=users_by_role,
        locations_total=sum(v for _, v in by_cat),
        locations_by_category={k.value: v for k, v in by_cat},
        locations_by_approval={k.value: v for k, v in by_approval},
        locations_by_status={k.value: v for k, v in by_status},
        updates_total=db.scalar(select(func.count(LocationUpdate.id))) or 0,
        updates_last_24h=db.scalar(
            select(func.count(LocationUpdate.id)).where(LocationUpdate.created_at >= now() - timedelta(hours=24))
        )
        or 0,
    )
