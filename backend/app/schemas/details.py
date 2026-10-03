"""Schemas for category-specific data (ration stock, museum, EV, pharmacy)."""
from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ChargingType, LocationStatus, QueueLevel, StockLevel
from app.utils.text import normalize_name


def _validate_http_url(value: str | None) -> str | None:
    if value is None:
        return value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("guide_url must be an http(s) URL")
    return value


# ---------------- ration shops ----------------
class RationStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rice: StockLevel
    wheat: StockLevel
    dal: StockLevel
    other_items: dict[str, StockLevel]


class RationStockUpdate(BaseModel):
    """Stock + overall status + queue in ONE request. Omitted fields are left unchanged."""

    rice: StockLevel | None = None
    wheat: StockLevel | None = None
    dal: StockLevel | None = None
    other_items: dict[str, StockLevel] | None = Field(
        default=None, description="Replaces the whole 'other essential items' map when provided"
    )
    status: LocationStatus | None = Field(
        default=None, description="Overall stock status; derived from rice/wheat/dal when omitted"
    )
    queue_level: QueueLevel | None = None
    note: str | None = Field(default=None, max_length=300)

    @field_validator("other_items")
    @classmethod
    def check_items(cls, value: dict[str, StockLevel] | None) -> dict[str, StockLevel] | None:
        if value is None:
            return value
        if len(value) > 30:
            raise ValueError("at most 30 other items")
        cleaned: dict[str, StockLevel] = {}
        for name, level in value.items():
            key = normalize_name(name)
            if not key or len(key) > 60:
                raise ValueError("item names must be 1-60 characters")
            cleaned[key] = level
        return cleaned

    @model_validator(mode="after")
    def at_least_one(self) -> RationStockUpdate:
        if not (self.model_fields_set - {"note"}):
            raise ValueError("at least one field must be provided")
        return self


# ---------------- museums ----------------
class MuseumOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    opening_hours: str | None
    historical_description: str | None
    guide_available: bool
    guide_url: str | None
    guide_content_id: str | None
    crowd_level: QueueLevel


class MuseumUpdate(BaseModel):
    """Open/closed status, crowd level and museum info. Text fields accept null to clear."""

    status: LocationStatus | None = Field(default=None, description="Open/closed state, e.g. AVAILABLE or CLOSED")
    queue_level: QueueLevel | None = Field(default=None, description="Visitor crowd level")
    opening_hours: str | None = Field(default=None, max_length=255)
    historical_description: str | None = Field(default=None, max_length=10_000)
    guide_available: bool | None = None
    guide_url: str | None = Field(default=None, max_length=500)
    guide_content_id: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=300)

    _check_url = field_validator("guide_url")(_validate_http_url)

    @model_validator(mode="after")
    def at_least_one(self) -> MuseumUpdate:
        if not (self.model_fields_set - {"note"}):
            raise ValueError("at least one field must be provided")
        return self


class MuseumInput(BaseModel):
    """Museum details accepted when creating a location."""

    opening_hours: str | None = Field(default=None, max_length=255)
    historical_description: str | None = Field(default=None, max_length=10_000)
    guide_available: bool = False
    guide_url: str | None = Field(default=None, max_length=500)
    guide_content_id: str | None = Field(default=None, max_length=100)

    _check_url = field_validator("guide_url")(_validate_http_url)


class GuideOut(BaseModel):
    location_id: int
    name: str
    guide_available: bool
    guide_url: str | None
    guide_content_id: str | None
    opening_hours: str | None
    historical_description: str | None


# ---------------- EV ----------------
class EVStationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_plugs: int
    occupied_plugs: int
    available_plugs: int
    charging_type: ChargingType
    estimated_wait_minutes: int


class EVAvailabilityUpdate(BaseModel):
    """available_plugs is always derived: total_plugs - occupied_plugs."""

    total_plugs: int | None = Field(default=None, ge=0, le=500)
    occupied_plugs: int | None = Field(default=None, ge=0, le=500)
    charging_type: ChargingType | None = None
    estimated_wait_minutes: int | None = Field(default=None, ge=0, le=1440)
    status: LocationStatus | None = None
    queue_level: QueueLevel | None = None
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_update(self) -> EVAvailabilityUpdate:
        if not (self.model_fields_set - {"note"}):
            raise ValueError("at least one field must be provided")
        if (
            self.total_plugs is not None
            and self.occupied_plugs is not None
            and self.occupied_plugs > self.total_plugs
        ):
            raise ValueError("occupied_plugs cannot exceed total_plugs")
        return self


class EVStationInput(BaseModel):
    total_plugs: int = Field(ge=0, le=500)
    occupied_plugs: int = Field(default=0, ge=0, le=500)
    charging_type: ChargingType = ChargingType.MIXED
    estimated_wait_minutes: int = Field(default=0, ge=0, le=1440)

    @model_validator(mode="after")
    def occupied_not_above_total(self) -> EVStationInput:
        if self.occupied_plugs > self.total_plugs:
            raise ValueError("occupied_plugs cannot exceed total_plugs")
        return self


# ---------------- pharmacy ----------------
class MedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    medicine_name: str
    is_available: bool
    quantity: int | None
    prescription_required: bool
    last_stock_update: datetime


class MedicineItem(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=200)
    is_available: bool = True
    quantity: int | None = Field(default=None, ge=0, le=1_000_000, description="Omit if unknown")
    prescription_required: bool | None = Field(default=None, description="Defaults to false for new medicines")

    @field_validator("medicine_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("medicine_name must not be blank")
        return value

    @model_validator(mode="after")
    def zero_means_unavailable(self) -> MedicineItem:
        if self.quantity == 0:
            self.is_available = False
        return self


class PharmacyInventoryUpdate(BaseModel):
    """Upsert medicines (by name), optionally remove some, and update status/queue in one call."""

    items: list[MedicineItem] = Field(default_factory=list, max_length=500)
    remove: list[str] = Field(default_factory=list, max_length=500)
    status: LocationStatus | None = None
    queue_level: QueueLevel | None = None
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def at_least_one(self) -> PharmacyInventoryUpdate:
        if not (self.items or self.remove or self.status or self.queue_level):
            raise ValueError("provide items, remove, status or queue_level")
        return self


class MedicineSearchResult(BaseModel):
    location_id: int
    pharmacy_name: str
    address: str
    phone: str | None
    latitude: float
    longitude: float
    status: LocationStatus
    queue_level: QueueLevel
    last_updated: datetime
    distance_km: float | None
    medicine_name: str
    is_available: bool
    quantity: int | None
    prescription_required: bool
    last_stock_update: datetime
