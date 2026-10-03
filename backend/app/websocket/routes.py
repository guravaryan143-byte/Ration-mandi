from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.enums import Category
from app.services.location_service import get_visible_location
from app.utils.errors import AppError
from app.websocket.manager import build_message, manager

router = APIRouter()


def _snapshot(factory: Callable[[], Session], location_id: int) -> dict | None:
    with factory() as db:
        try:
            return build_message(get_visible_location(db, location_id), event="snapshot")
        except AppError:
            return None


@router.websocket("/ws/locations/{location_id}")
async def location_updates(
    websocket: WebSocket,
    location_id: int,
    factory: Callable[[], Session] = Depends(get_session_factory),
) -> None:
    """Live feed for one location. Sends a `snapshot` on connect, then `location_update` events."""
    snapshot = await run_in_threadpool(_snapshot, factory, location_id)
    if snapshot is None:
        await websocket.close(code=4404, reason="Location not found")
        return
    await manager.connect(location_id, websocket)
    try:
        await websocket.send_json(snapshot)
        while True:
            text = await websocket.receive_text()  # keeps the socket open; clients may send "ping"
            if text.strip().lower() == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(location_id, websocket)
