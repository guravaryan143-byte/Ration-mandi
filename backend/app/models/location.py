from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ApprovalStatus, Category, LocationStatus, QueueLevel
from app.models.types import UTCDateTime, enum_type, utc_now


class Location(Base):
    """Generic location/service. Category-specific data lives in 1:1 / 1:N detail tables."""

    __tablename__ = "locations"
    __table_args__ = (
        # Target of the composite FKs that pin detail rows to the right category.
        UniqueConstraint("id", "category", name="uq_locations_id_category"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        Index("ix_locations_lat_lon", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[Category] = mapped_column(enum_type(Category, "category"), index=True)
    address: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LocationStatus] = mapped_column(
        enum_type(LocationStatus, "location_status"), default=LocationStatus.AVAILABLE, index=True
    )
    queue_level: Mapped[QueueLevel] = mapped_column(
        enum_type(QueueLevel, "queue_level"), default=QueueLevel.NOT_APPLICABLE, index=True
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        enum_type(ApprovalStatus, "approval_status"), default=ApprovalStatus.PENDING, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500))
    last_updated: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime)  # soft delete keeps the audit trail

    owner = relationship("User", back_populates="locations")
    ration_stock = relationship(
        "RationStock", back_populates="location", uselist=False, cascade="all, delete-orphan"
    )
    museum = relationship(
        "MuseumDetails", back_populates="location", uselist=False, cascade="all, delete-orphan"
    )
    ev_station = relationship(
        "EVStationDetails", back_populates="location", uselist=False, cascade="all, delete-orphan"
    )
    medicines = relationship(
        "PharmacyMedicine",
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="PharmacyMedicine.medicine_name",
    )
    updates = relationship("LocationUpdate", back_populates="location", order_by="LocationUpdate.id.desc()")
