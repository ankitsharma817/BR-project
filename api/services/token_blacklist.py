"""
Redis-backed JWT token blacklist.
Revoked tokens are stored until their natural expiry.
"""
import logging
from jose import jwt, JWTError
from ..config import settings
from ..utils.constants import JWT_ALGORITHM

logger = logging.getLogger(__name__)


class TokenBlacklist:
    _PREFIX = "blacklist:"

    def __init__(self):
        import redis as redis_lib
        self._redis = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)

    def revoke(self, token: str) -> None:
        """Add token to blacklist, expiring when the JWT itself expires."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
            import time
            ttl = int(payload.get("exp", 0) - time.time())
            if ttl > 0:
                self._redis.setex(f"{self._PREFIX}{token}", ttl, "1")
        except JWTError:
            pass  # Already invalid; no need to blacklist

    def is_revoked(self, token: str) -> bool:
        try:
            return self._redis.exists(f"{self._PREFIX}{token}") == 1
        except Exception as e:
            logger.warning("Blacklist check failed: %s", e)
            return False


_blacklist: TokenBlacklist | None = None


def get_blacklist() -> TokenBlacklist:
    global _blacklist
    if _blacklist is None:
        _blacklist = TokenBlacklist()
    return _blacklist
