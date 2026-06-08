import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.feedback import FeedbackCreate, FeedbackUpdate, FeedbackResponse
from ..schemas.common import ApiResponse, MessageResponse
from ..services.feedback_service import FeedbackService

router = APIRouter(prefix="/proposals", tags=["feedback"])


@router.post("/{proposal_id}/feedback", response_model=ApiResponse[FeedbackResponse], status_code=201)
async def submit_feedback(
    proposal_id: uuid.UUID,
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FeedbackService(db)
    fb = svc.create_feedback(proposal_id, current_user.id, data)
    return ApiResponse(data=FeedbackResponse.model_validate(fb), message="Feedback submitted")


@router.get("/{proposal_id}/feedback", response_model=ApiResponse[list[FeedbackResponse]])
async def get_feedbacks(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FeedbackService(db)
    fbs = svc.list_feedbacks(proposal_id)
    return ApiResponse(data=[FeedbackResponse.model_validate(f) for f in fbs])


@router.put("/{proposal_id}/feedback/{feedback_id}", response_model=ApiResponse[FeedbackResponse])
async def update_feedback(
    proposal_id: uuid.UUID,
    feedback_id: uuid.UUID,
    data: FeedbackUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FeedbackService(db)
    fb = svc.update_feedback(feedback_id, current_user.id, data)
    return ApiResponse(data=FeedbackResponse.model_validate(fb))


@router.post("/feedback/{feedback_id}/mark-useful", response_model=MessageResponse)
async def mark_useful(
    feedback_id: uuid.UUID,
    useful: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    FeedbackService(db).mark_useful(feedback_id, useful)
    return MessageResponse(message="Feedback marked as useful" if useful else "Feedback marked as not useful")
