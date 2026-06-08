import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..utils.constants import BRStatus, RequirementCategory, RequirementPriority


class RequirementCreate(BaseModel):
    text: str
    category: RequirementCategory
    priority: RequirementPriority = RequirementPriority.MEDIUM


class RequirementUpdate(BaseModel):
    text: Optional[str] = None
    category: Optional[RequirementCategory] = None
    priority: Optional[RequirementPriority] = None


class RequirementResponse(BaseModel):
    id: uuid.UUID
    text: str
    category: str
    priority: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BRCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None


class BRUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BRStatus] = None
    deadline: Optional[datetime] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None


class BRResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    deadline: Optional[datetime]
    budget_min: Optional[float]
    budget_max: Optional[float]
    created_at: datetime
    updated_at: datetime
    requirement_count: int = 0
    proposal_count: int = 0

    model_config = {"from_attributes": True}


class BRDetailResponse(BRResponse):
    requirements: list[RequirementResponse] = []
