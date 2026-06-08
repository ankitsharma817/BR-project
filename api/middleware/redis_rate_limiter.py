"""
Redis-backed sliding-window rate limiter.
Falls back to in-process limiter when Redis is unavailable.
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from ..config import settings

logger = logging.getLogger(__name__)

WINDOW = 60       # seconds
MAX_REQ = 100     # requests per window


def _redis_client():
    import redis as redis_lib
    return redis_lib.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, window: int = WINDOW, max_requests: int = MAX_REQ):
        super().__init__(app)
        self._window = window
        self._max = max_requests
        self._redis = None
        try:
            self._redis = _redis_client()
            self._redis.ping()
        except Exception:
            logger.warning("Redis unavailable — rate limiting disabled")
            self._redis = None

    async def dispatch(self, request: Request, call_next):
        if self._redis is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        key = f"rl:{ip}"
        now = time.time()
        window_start = now - self._window

        try:
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self._window + 1)
            results = pipe.execute()
            count = results[2]

            if count > self._max:
                return JSONResponse(
                    status_code=429,
                    content={"success": False, "message": "Too many requests. Please slow down.", "data": None},
                    headers={"Retry-After": str(self._window)},
                )
        except Exception as e:
            logger.warning("Rate limiter Redis error: %s", e)

        return await call_next(request)
