from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: PageMeta | None = None


def ok(data: T, meta: PageMeta | None = None) -> dict:
    """Envelope helper; returned dicts are validated by each route's response_model."""
    return {"success": True, "data": data, "meta": meta}


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody
