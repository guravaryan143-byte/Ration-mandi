"""In-process WebSocket fan-out, one channel per location."""
from __future__ import annotations

import logging
from collections import defaultdict

from fastapi import BackgroundTasks, WebSocket

from app.models.location import Location

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, location_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[location_id].add(websocket)

    def disconnect(self, location_id: int, websocket: WebSocket) -> None:
        room = self._rooms.get(location_id)
        if room:
            room.discard(websocket)
            if not room:
                self._rooms.pop(location_id, None)

    async def broadcast(self, location_id: int, message: dict) -> None:
        for ws in list(self._rooms.get(location_id, ())):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 - a dead client must not break the others
                logger.debug("Dropping broken websocket for location %s", location_id)
                self.disconnect(location_id, ws)


manager = ConnectionManager()


def build_message(location: Location, event: str = "location_update") -> dict:
    from app.services.location_service import to_out

    return {"event": event, "location_id": location.id, "data": to_out(location).model_dump(mode="json")}


def queue_broadcast(background_tasks: BackgroundTasks, location: Location) -> None:
    """Schedule a broadcast to run after the HTTP response (the payload is built now, post-commit)."""
    background_tasks.add_task(manager.broadcast, location.id, build_message(location))
