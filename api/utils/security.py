import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings
from .constants import JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access", **(extra or {})}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])


def is_token_valid(token: str) -> bool:
    try:
        decode_token(token)
        return True
    except JWTError:
        return False


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
