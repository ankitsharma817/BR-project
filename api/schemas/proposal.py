import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class ProposalCreate(BaseModel):
    vendor_name: str
    vendor_contact: Optional[str] = None
    vendor_email: Optional[EmailStr] = None
    proposed_cost: Optional[float] = None
    proposed_timeline_months: Optional[int] = None


class ProposalResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    vendor_name: str
    vendor_contact: Optional[str]
    vendor_email: Optional[str]
    filename: str
    proposed_cost: Optional[float]
    proposed_timeline_months: Optional[int]
    status: str
    overall_score: Optional[float] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ProposalDetailResponse(ProposalResponse):
    extracted_text: Optional[str] = None
    requirement_count: int = 0
