import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.user import User, Session as UserSession, LoginAttempt
from ..utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..utils.constants import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, email: str, password: str, full_name: str, role: str = "user") -> User:
        if self.get_user_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _is_locked_out(self, user: User) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        recent_failures = (
            self.db.query(LoginAttempt)
            .filter(
                LoginAttempt.user_id == user.id,
                LoginAttempt.success == False,
                LoginAttempt.attempted_at >= cutoff,
            )
            .count()
        )
        return recent_failures >= MAX_LOGIN_ATTEMPTS

    def _record_attempt(self, user: User, success: bool, ip: str | None = None) -> None:
        attempt = LoginAttempt(user_id=user.id, success=success, ip_address=ip)
        self.db.add(attempt)
        self.db.commit()

    def login(self, email: str, password: str, ip: str | None = None) -> dict:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")
        if self._is_locked_out(user):
            raise HTTPException(status_code=429, detail="Account temporarily locked. Try again later.")
        if not verify_password(password, user.hashed_password):
            self._record_attempt(user, False, ip)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        self._record_attempt(user, True, ip)
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)
        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def logout(self, refresh_token: str) -> None:
        session = self.db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()
        if session:
            session.revoked = True
            self.db.commit()

    def refresh_access_token(self, refresh_token: str) -> dict:
        session = (
            self.db.query(UserSession)
            .filter(
                UserSession.refresh_token == refresh_token,
                UserSession.revoked == False,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

        access_token = create_access_token(str(session.user_id))
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def update_password(self, user: User, new_password: str) -> None:
        user.hashed_password = hash_password(new_password)
        self.db.commit()
