from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.utils.errors import AppError


def commit_or_raise(db: Session) -> None:
    """Commit and translate database failures into API errors (rolling back first)."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DATA_CONFLICT", "The change conflicts with existing data or a rule") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise AppError(500, "DATABASE_ERROR", "A database error occurred") from exc
