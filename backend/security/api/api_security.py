"""WebSecKit — API error sanitization and pagination."""

from __future__ import annotations

from ..config.security_config import MAX_BODY_BYTES, MAX_PAGE_SIZE


class ApiError(Exception):
    def __init__(self, status: int, message: str, expose: bool | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.expose = status < 500 if expose is None else expose


def public_error_message(error: Exception) -> tuple[int, str]:
    if isinstance(error, ApiError) and error.expose:
        return error.status, str(error)
    status = getattr(error, "status", 500)
    if 400 <= int(status) < 500:
        return int(status), "Invalid request."
    return 500, "Internal server error."


def paginate(items: list[object], page: int, page_size: int) -> dict[str, object]:
    size = min(max(page_size, 1), MAX_PAGE_SIZE)
    current = max(page, 1)
    start = (current - 1) * size
    return {"items": items[start : start + size], "page": current, "page_size": size, "total": len(items)}


def assert_body_size(byte_length: int) -> None:
    if byte_length > MAX_BODY_BYTES:
        raise ApiError(413, "Payload too large.")
