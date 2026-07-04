"""Application error hierarchy and FastAPI handlers producing the API error envelope.

Every non-2xx response has the shape:
    {"error": {"code": "...", "message": "...", "detail": ...}}
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal"

    def __init__(self, message: str, detail=None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class InvalidPdfError(AppError):
    status_code = 400
    code = "invalid_pdf"


class EncryptedPdfError(AppError):
    status_code = 400
    code = "encrypted_pdf"


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_failed"


class RenderError(AppError):
    status_code = 500
    code = "render_failed"


def _envelope(code: str, message: str, detail=None) -> dict:
    return {"error": {"code": code, "message": message, "detail": detail}}


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_envelope("validation_failed", "Invalid request.", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_envelope("internal", "An unexpected error occurred."),
        )
