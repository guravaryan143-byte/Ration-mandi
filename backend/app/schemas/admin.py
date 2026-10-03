from __future__ import annotations

from pydantic import BaseModel, Field


class RejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class UserActiveUpdate(BaseModel):
    is_active: bool


class StatsOut(BaseModel):
    users_total: int
    users_by_role: dict[str, int]
    locations_total: int
    locations_by_category: dict[str, int]
    locations_by_approval: dict[str, int]
    locations_by_status: dict[str, int]
    updates_total: int
    updates_last_24h: int
