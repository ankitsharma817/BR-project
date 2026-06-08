import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from jose import JWTError

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Validation error", "data": errors},
    )


async def http_exception_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.error("DB integrity error: %s", exc)
    return JSONResponse(
        status_code=409,
        content={"success": False, "message": "Data conflict — record already exists or constraint violated", "data": None},
    )
