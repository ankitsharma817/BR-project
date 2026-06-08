import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Simple in-process sliding-window rate limiter
# For production, replace with Redis-based limiter
_request_log: dict[str, list[float]] = defaultdict(list)
WINDOW_SECONDS = 60
MAX_REQUESTS = 100


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - WINDOW_SECONDS
        log = _request_log[client_ip]
        # Drop timestamps outside the window
        _request_log[client_ip] = [t for t in log if t > window_start]
        if len(_request_log[client_ip]) >= MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"success": False, "message": "Too many requests. Slow down.", "data": None},
            )
        _request_log[client_ip].append(now)
        return await call_next(request)
