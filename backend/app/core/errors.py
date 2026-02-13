from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("carepath.errors")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    async def _http_error_response(request: Request, status_code: int, detail):
        rid = _request_id(request)
        message = detail if isinstance(detail, str) else "Request error"
        body = {
            "detail": message,
            "error": {
                "code": f"http_{status_code}",
                "message": message,
                "details": detail if not isinstance(detail, str) else None,
                "request_id": rid,
            },
        }
        response = JSONResponse(status_code=status_code, content=body)
        if rid:
            response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return await _http_error_response(request, exc.status_code, exc.detail)

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await _http_error_response(request, exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        rid = _request_id(request)
        body = {
            "detail": "Validation error",
            "error": {
                "code": "validation_error",
                "message": "Validation error",
                "details": exc.errors(),
                "request_id": rid,
            },
        }
        response = JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body)
        if rid:
            response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        rid = _request_id(request)
        logger.exception(
            "unhandled_exception",
            extra={"request_id": rid, "path": request.url.path, "method": request.method},
        )
        body = {
            "detail": "Internal server error",
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
                "details": None,
                "request_id": rid,
            },
        }
        response = JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body)
        if rid:
            response.headers["X-Request-ID"] = rid
        return response
