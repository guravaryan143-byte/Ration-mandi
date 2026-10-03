from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ApprovalStatus, Category, LocationStatus, QueueLevel, UpdateType
from app.schemas.details import (
    EVStationInput,
    EVStationOut,
    MedicineItem,
    MedicineOut,
    MuseumInput,
    MuseumOut,
    RationStockOut,
    RationStockUpdate,
)


class LocationOut(BaseModel):
    """Every location response carries status, queue_level and last_updated."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Category
    address: str
    latitude: float
    longitude: float
    phone: str | None
    description: str | None
    status: LocationStatus
    queue_level: QueueLevel
    last_updated: datetime
    owner_id: int
    created_at: datetime
    approval_status: ApprovalStatus
    rejection_reason: str | None = None
    distance_km: float | None = None
    ration_stock: RationStockOut | None = None
    museum: MuseumOut | None = None
    ev_station: EVStationOut | None = None
    medicines: list[MedicineOut] = []


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: Category
    address: str = Field(min_length=1, max_length=500)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=32, pattern=r"^[0-9+()\-\s]{3,32}$")
    description: str | None = Field(default=None, max_length=5000)
    status: LocationStatus = LocationStatus.AVAILABLE
    queue_level: QueueLevel = QueueLevel.NOT_APPLICABLE
    # Category-specific data (must match `category`)
    ration_stock: RationStockUpdate | None = None
    museum: MuseumInput | None = None
    ev_station: EVStationInput | None = None
    medicines: list[MedicineItem] = Field(default_factory=list, max_length=500)

    @field_validator("name", "address")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def details_match_category(self) -> LocationCreate:
        allowed = {
            Category.RATION_SHOP: "ration_stock",
            Category.MUSEUM_MONUMENT: "museum",
            Category.EV_CHARGING: "ev_station",
            Category.PHARMACY: "medicines",
        }[self.category]
        for field in ("ration_stock", "museum", "ev_station", "medicines"):
            if field != allowed and getattr(self, field):
                raise ValueError(f"'{field}' is not valid for category {self.category.value}")
        if self.category == Category.EV_CHARGING and self.ev_station is None:
            raise ValueError("ev_station (with total_plugs) is required for EV_CHARGING")
        return self


class LocationProfileUpdate(BaseModel):
    """Descriptive fields only; status/queue/stock have dedicated endpoints."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=32, pattern=r"^[0-9+()\-\s]{3,32}$")
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def at_least_one(self) -> LocationProfileUpdate:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class StatusUpdate(BaseModel):
    status: LocationStatus | None = None
    queue_level: QueueLevel | None = None
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def at_least_one(self) -> StatusUpdate:
        if self.status is None and self.queue_level is None:
            raise ValueError("provide status and/or queue_level")
        return self


class LocationUpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    updated_by: int
    update_type: UpdateType
    field_name: str
    previous_value: str | None
    new_value: str | None
    note: str | None
    created_at: datetime
