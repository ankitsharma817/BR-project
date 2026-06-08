import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RequirementMatchingResponse(BaseModel):
    id: uuid.UUID
    br_requirement_text: str
    br_requirement_category: str
    br_requirement_priority: str
    proposal_requirement_text: Optional[str]
    score: float
    label: str
    explanation: Optional[str]

    model_config = {"from_attributes": True}


class MatchingResultResponse(BaseModel):
    id: uuid.UUID
    proposal_id: uuid.UUID
    overall_score: float
    functional_score: Optional[float]
    technical_score: Optional[float]
    compliance_score: Optional[float]
    security_score: Optional[float]
    timeline_score: Optional[float]
    resource_score: Optional[float]
    deliverables_score: Optional[float]
    executive_summary: Optional[str]
    calculated_at: datetime
    version: int
    requirement_matchings: list[RequirementMatchingResponse] = []

    model_config = {"from_attributes": True}


class RiskItem(BaseModel):
    level: str
    description: str
    category: Optional[str] = None


class RecommendationItem(BaseModel):
    priority: str
    action: str
    reason: Optional[str] = None


class MatchAnalysisResponse(BaseModel):
    result_id: uuid.UUID
    risks: list[RiskItem] = []
    recommendations: list[RecommendationItem] = []
    strengths: list[str] = []
    gaps: list[str] = []

    model_config = {"from_attributes": True}


class CompareRequest(BaseModel):
    proposal_ids: list[uuid.UUID]
