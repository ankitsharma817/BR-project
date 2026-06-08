import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("br_match.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Process-Time"] = f"{duration_ms:.1f}ms"
        return response
