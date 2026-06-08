import uuid
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from .database import get_db
from .utils.security import decode_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    from .models.user import User
    user = db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user
