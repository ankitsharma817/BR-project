from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.auth import UserLogin, UserCreate, UserProfile, TokenResponse, RefreshTokenRequest, PasswordResetRequest, PasswordReset
from ..schemas.common import ApiResponse, MessageResponse
from ..services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserProfile], status_code=201)
async def register(data: UserCreate, db: Session = Depends(get_db)):
    svc = AuthService(db)
    user = svc.create_user(data.email, data.password, data.full_name)
    return ApiResponse(data=UserProfile.model_validate(user), message="User registered successfully")


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    svc = AuthService(db)
    ip = request.client.host if request.client else None
    tokens = svc.login(data.email, data.password, ip)
    return ApiResponse(data=TokenResponse(**tokens))


@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    AuthService(db).logout(body.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh-token", response_model=ApiResponse[dict])
async def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    svc = AuthService(db)
    result = svc.refresh_access_token(body.refresh_token)
    return ApiResponse(data=result)


@router.get("/profile", response_model=ApiResponse[UserProfile])
async def get_profile(current_user: User = Depends(get_current_user)):
    return ApiResponse(data=UserProfile.model_validate(current_user))


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(body: PasswordResetRequest, db: Session = Depends(get_db)):
    # In production: send reset email. We return generic message to prevent user enumeration.
    return MessageResponse(message="If this email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: PasswordReset, db: Session = Depends(get_db)):
    # Token verification would be implemented with a dedicated reset-token table
    return MessageResponse(message="Password reset functionality requires email setup.")
