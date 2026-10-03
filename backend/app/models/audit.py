from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UpdateType
from app.models.types import UTCDateTime, enum_type, utc_now


class LocationUpdate(Base):
    """Audit trail: one row per changed field."""

    __tablename__ = "location_updates"
    __table_args__ = (Index("ix_location_updates_location_created", "location_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), index=True)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    update_type: Mapped[UpdateType] = mapped_column(enum_type(UpdateType, "update_type"))
    field_name: Mapped[str] = mapped_column(String(120))
    previous_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    location = relationship("Location", back_populates="updates")
    user = relationship("User")
