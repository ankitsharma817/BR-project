import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from ..utils.constants import FeedbackType


class FeedbackCreate(BaseModel):
    feedback_type: FeedbackType
    rating: Optional[int] = None
    comment: Optional[str] = None
    corrected_score: Optional[float] = None
    original_score: Optional[float] = None

    @field_validator("rating")
    @classmethod
    def valid_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 1 <= v <= 5:
            raise ValueError("rating must be between 1 and 5")
        return v

    @field_validator("corrected_score")
    @classmethod
    def valid_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("corrected_score must be between 0.0 and 1.0")
        return v


class FeedbackUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None
    corrected_score: Optional[float] = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    proposal_id: uuid.UUID
    feedback_type: str
    rating: Optional[int]
    comment: Optional[str]
    corrected_score: Optional[float]
    original_score: Optional[float]
    is_useful: Optional[bool]
    created_at: datetime

    model_config = {"from_attributes": True}
