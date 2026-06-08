import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from ..utils.validators import validate_password_strength


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v
