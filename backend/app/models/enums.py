from __future__ import annotations

import enum


class Category(str, enum.Enum):
    RATION_SHOP = "RATION_SHOP"
    MUSEUM_MONUMENT = "MUSEUM_MONUMENT"
    EV_CHARGING = "EV_CHARGING"
    PHARMACY = "PHARMACY"


class LocationStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    CLOSED = "CLOSED"
    BUSY = "BUSY"
    MAINTENANCE = "MAINTENANCE"


class QueueLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OWNER = "OWNER"  # shopkeeper / location owner
    ADMIN = "ADMIN"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StockLevel(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class ChargingType(str, enum.Enum):
    AC_SLOW = "AC_SLOW"
    DC_FAST = "DC_FAST"
    MIXED = "MIXED"


class UpdateType(str, enum.Enum):
    CREATED = "CREATED"
    PROFILE = "PROFILE"
    STATUS = "STATUS"
    QUEUE = "QUEUE"
    STOCK = "STOCK"
    MUSEUM = "MUSEUM"
    EV_AVAILABILITY = "EV_AVAILABILITY"
    PHARMACY_INVENTORY = "PHARMACY_INVENTORY"
    MODERATION = "MODERATION"
    DELETED = "DELETED"
