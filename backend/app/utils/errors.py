from __future__ import annotations


class AppError(Exception):
    """Domain error rendered as {"success": false, "error": {"code", "message"}}."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
        details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers
        self.details = details


def not_found(message: str = "Location not found") -> AppError:
    return AppError(404, "LOCATION_NOT_FOUND", message)


def forbidden(message: str = "You do not have permission to perform this action") -> AppError:
    return AppError(403, "FORBIDDEN", message)
