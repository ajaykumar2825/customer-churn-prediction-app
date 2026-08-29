"""Domain exceptions and the FastAPI exception handlers that map them to JSON."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ChurnAPIError(Exception):
    """Base class for every intentionally raised HTTP error."""

    def __init__(self, message: str, code: str = "api_error", http_status: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status


class NotFoundError(ChurnAPIError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            f"{resource} '{identifier}' was not found",
            code="not_found",
            http_status=status.HTTP_404_NOT_FOUND,
        )


class ValidationFailed(ChurnAPIError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, code="validation_failed", http_status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class RateLimited(ChurnAPIError):
    def __init__(self) -> None:
        super().__init__("Rate limit exceeded. Retry shortly.", code="rate_limited", http_status=status.HTTP_429_TOO_MANY_REQUESTS)


class ModelNotReady(ChurnAPIError):
    def __init__(self) -> None:
        super().__init__("Model artefacts have not been loaded yet.", code="model_not_ready", http_status=status.HTTP_503_SERVICE_UNAVAILABLE)


def install_exception_handlers(app: FastAPI) -> None:
    """Attach all ``ChurnAPIError`` subclasses + a generic fallback."""

    @app.exception_handler(ChurnAPIError)
    async def handle_churn_error(request: Request, exc: ChurnAPIError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=exc.http_status,
            content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        del request, exc
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": {"code": "internal_error", "message": "An unexpected error occurred."}},
        )
