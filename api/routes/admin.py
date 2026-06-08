from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.common import ApiResponse
from ..services.admin_service import AdminService
from ..services.feedback_service import FeedbackService

router = APIRouter(tags=["admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return current_user


@router.get("/dashboard", response_model=ApiResponse[dict])
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = AdminService(db)
    return ApiResponse(data=svc.get_dashboard_stats())


@router.get("/dashboard/system-health", response_model=ApiResponse[dict])
async def system_health(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=AdminService(db).get_system_health())


@router.get("/dashboard/activities", response_model=ApiResponse[list])
async def activities(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=AdminService(db).get_recent_activities(limit))


@router.get("/admin/audit-logs", response_model=ApiResponse[dict])
async def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=AdminService(db).get_audit_logs(page, page_size))


@router.get("/admin/feedback-quality-report", response_model=ApiResponse[dict])
async def feedback_quality_report(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=FeedbackService(db).get_quality_metrics())


@router.get("/admin/ai-learning/stats", response_model=ApiResponse[dict])
async def ai_learning_stats(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=AdminService(db).get_ai_learning_stats())


@router.get("/admin/ai-learning/retraining-status", response_model=ApiResponse[dict])
async def retraining_status(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    # Placeholder — actual retraining pipeline would be a separate service
    return ApiResponse(data={"status": "idle", "last_retrained": None, "pending_corrections": 0})
