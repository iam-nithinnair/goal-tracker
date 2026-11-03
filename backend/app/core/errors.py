"""One error shape for the whole API (docs/04-api.md):
{"error": {"code": "...", "message": "...", "fields": {...}}}"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError as PostgrestError
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("goal_tracker")


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        super().__init__(message)


def not_found(what: str = "Resource") -> ApiError:
    # Other people's resources are reported as 404 too, so existence is never leaked.
    return ApiError(404, "not_found", f"{what} not found")


def validation_error(message: str, fields: dict[str, str] | None = None) -> ApiError:
    return ApiError(400, "validation_error", message, fields)


def _body(code: str, message: str, fields: dict[str, str] | None = None) -> dict:
    err: dict = {"code": code, "message": message}
    if fields:
        err["fields"] = fields
    return {"error": err}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(_body(exc.code, exc.message, exc.fields), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        fields: dict[str, str] = {}
        for e in exc.errors():
            loc = [str(p) for p in e["loc"] if p not in ("body", "query", "path")]
            fields[".".join(loc) or "request"] = e["msg"]
        return JSONResponse(
            _body("validation_error", "Some fields are invalid", fields), status_code=400
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        codes = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}
        return JSONResponse(
            _body(codes.get(exc.status_code, "http_error"), str(exc.detail)),
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(PostgrestError)
    async def _postgrest(_: Request, exc: PostgrestError):
        code = str(getattr(exc, "code", "") or "")
        if code in {"23514", "22007", "22008", "23502"}:  # check / date / not-null violations
            return JSONResponse(
                _body("validation_error", "The data violates a rule"), status_code=400
            )
        if code == "23505":  # unique violation
            return JSONResponse(_body("conflict", "That already exists"), status_code=409)
        log.exception("database error (%s)", code)
        return JSONResponse(_body("internal_error", "Something went wrong"), status_code=500)
