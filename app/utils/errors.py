"""Custom exception classes and error handlers."""

from __future__ import annotations

from typing import Any
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity": entity_name, "id": str(entity_id)},
        )


class LLMServiceError(AppException):
    """Raised when external LLM service fails or returns invalid format."""

    def __init__(self, message: str, provider: str, raw_response: str | None = None):
        super().__init__(
            message=f"LLM Provider [{provider}] error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"provider": provider, "raw_response": raw_response[:500] if raw_response else None},
        )


class EstimationEngineError(AppException):
    """Raised when an estimation calculation fails."""

    def __init__(self, message: str, model_name: str = "hybrid"):
        super().__init__(
            message=f"Estimation failed in {model_name}: {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"model": model_name},
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """FastAPI handler for custom AppException instances."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
        },
    )
