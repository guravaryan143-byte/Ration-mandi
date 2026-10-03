"""Small in-process sliding-window limiter for public search endpoints.

Per-process only; use a shared store (e.g. Redis) or a gateway when running several workers.
"""
from __future__ import annotations

import time
from collections import deque
from threading import Lock

from fastapi import Request

from app.config import get_settings
from app.utils.errors import AppError


class SlidingWindowLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            if len(self._hits) > 10_000:  # drop idle keys so memory stays bounded
                self._hits = {k: v for k, v in self._hits.items() if v and now - v[-1] <= self.window}
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def rate_limit(request: Request) -> None:
    limit = get_settings().rate_limit_per_minute
    if limit <= 0:
        return
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client, limit):
        raise AppError(429, "RATE_LIMITED", "Too many requests, please slow down", headers={"Retry-After": "60"})
