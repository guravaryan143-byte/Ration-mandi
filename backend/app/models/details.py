"""Category-specific tables.

Every table has a composite FK (location_id, category) -> locations(id, category) plus a
CHECK on `category`, so the database itself rejects e.g. a medicine row on a museum.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Category, ChargingType, StockLevel
from app.models.types import UTCDateTime, enum_type, utc_now


def _category_fk(table: str) -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["location_id", "category"],
        ["locations.id", "locations.category"],
        ondelete="CASCADE",
        name=f"fk_{table}_location_category",
    )


class RationStock(Base):
    __tablename__ = "ration_stock"
    __table_args__ = (
        _category_fk("ration_stock"),
        CheckConstraint("category = 'RATION_SHOP'", name="category_is_ration"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(unique=True, index=True)
    category: Mapped[Category] = mapped_column(
        enum_type(Category, "category"), default=Category.RATION_SHOP
    )
    rice: Mapped[StockLevel] = mapped_column(enum_type(StockLevel, "rice_level"), default=StockLevel.AVAILABLE)
    wheat: Mapped[StockLevel] = mapped_column(enum_type(StockLevel, "wheat_level"), default=StockLevel.AVAILABLE)
    dal: Mapped[StockLevel] = mapped_column(enum_type(StockLevel, "dal_level"), default=StockLevel.AVAILABLE)
    other_items: Mapped[dict] = mapped_column(JSON, default=dict)  # {"sugar": "AVAILABLE", ...}

    location = relationship("Location", back_populates="ration_stock")


class MuseumDetails(Base):
    __tablename__ = "museum_details"
    __table_args__ = (
        _category_fk("museum_details"),
        CheckConstraint("category = 'MUSEUM_MONUMENT'", name="category_is_museum"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(unique=True, index=True)
    category: Mapped[Category] = mapped_column(
        enum_type(Category, "category"), default=Category.MUSEUM_MONUMENT
    )
    opening_hours: Mapped[str | None] = mapped_column(String(255))
    historical_description: Mapped[str | None] = mapped_column(Text)
    guide_available: Mapped[bool] = mapped_column(Boolean, default=False)
    guide_url: Mapped[str | None] = mapped_column(String(500))
    guide_content_id: Mapped[str | None] = mapped_column(String(100))

    location = relationship("Location", back_populates="museum")

    @property
    def crowd_level(self):  # visitor crowd level is the location's queue level
        return self.location.queue_level


class EVStationDetails(Base):
    __tablename__ = "ev_station_details"
    __table_args__ = (
        _category_fk("ev_station_details"),
        CheckConstraint("category = 'EV_CHARGING'", name="category_is_ev"),
        CheckConstraint("total_plugs >= 0", name="total_plugs_non_negative"),
        CheckConstraint("occupied_plugs >= 0", name="occupied_plugs_non_negative"),
        CheckConstraint("occupied_plugs <= total_plugs", name="occupied_lte_total"),
        CheckConstraint("estimated_wait_minutes >= 0", name="wait_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(unique=True, index=True)
    category: Mapped[Category] = mapped_column(
        enum_type(Category, "category"), default=Category.EV_CHARGING
    )
    total_plugs: Mapped[int] = mapped_column(Integer)
    occupied_plugs: Mapped[int] = mapped_column(Integer, default=0)
    charging_type: Mapped[ChargingType] = mapped_column(
        enum_type(ChargingType, "charging_type"), default=ChargingType.MIXED
    )
    estimated_wait_minutes: Mapped[int] = mapped_column(Integer, default=0)

    location = relationship("Location", back_populates="ev_station")

    @property
    def available_plugs(self) -> int:
        """available_plugs = total_plugs - occupied_plugs (always derived, never stored)."""
        return self.total_plugs - self.occupied_plugs


class PharmacyMedicine(Base):
    """Inventory availability only. No patient or prescription data is ever stored."""

    __tablename__ = "pharmacy_medicines"
    __table_args__ = (
        _category_fk("pharmacy_medicines"),
        CheckConstraint("category = 'PHARMACY'", name="category_is_pharmacy"),
        CheckConstraint("quantity IS NULL OR quantity >= 0", name="quantity_non_negative"),
        UniqueConstraint("location_id", "name_key", name="uq_pharmacy_medicines_location_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(index=True)
    category: Mapped[Category] = mapped_column(enum_type(Category, "category"), default=Category.PHARMACY)
    medicine_name: Mapped[str] = mapped_column(String(200))
    name_key: Mapped[str] = mapped_column(String(200), index=True)  # normalised for search
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    prescription_required: Mapped[bool] = mapped_column(Boolean, default=False)
    last_stock_update: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    location = relationship("Location", back_populates="medicines")
