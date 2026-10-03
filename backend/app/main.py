from __future__ import annotations

from fastapi import FastAPI  # type: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[reportMissingImports]

from app.config import get_settings
from app.routers import admin, auth, ev, locations, museums, owner, pharmacies, ration
from app.utils.handlers import register_exception_handlers
from app.websocket.routes import router as ws_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Live availability & queue status for ration shops, museums/monuments, EV charging "
            "stations and pharmacies. Citizens search without logging in; owners update live data; "
            "admins moderate. WebSocket: `/ws/locations/{id}`."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,  # bearer tokens, no cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    for module in (auth, locations, ration, museums, ev, pharmacies, owner, admin):
        app.include_router(module.router)
    app.include_router(ws_router)

    @app.get("/health", tags=["Health"])
    def health() -> dict:
        return {"success": True, "data": {"status": "ok"}}

    return app


app = create_app()
