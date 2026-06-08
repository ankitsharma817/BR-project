"""
Full-text search and advanced filtering across BR projects and proposals.
GET /api/v1/search?q=...&type=br|proposal|all&page=1&page_size=20
GET /api/v1/proposals/{id}/match/filter — filter requirement matchings by label/category
GET /api/v1/br-projects/{id}/proposals/ranked — proposals sorted by score
"""
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.br import BRProject, BRRequirement
from ..models.proposal import Proposal
from ..models.matching import MatchingResult, RequirementMatching
from ..schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(tags=["search"])


@router.get("/search", response_model=ApiResponse[dict])
async def global_search(
    q: str = Query(..., min_length=2, description="Search query"),
    type: str = Query("all", regex="^(all|br|proposal)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results: dict = {"br_projects": [], "proposals": [], "total": 0}
    pattern = f"%{q}%"

    if type in ("all", "br"):
        br_q = db.query(BRProject).filter(
            BRProject.is_deleted == False,
            or_(
                BRProject.title.ilike(pattern),
                BRProject.description.ilike(pattern),
            ),
        )
        if current_user.role != "admin":
            br_q = br_q.filter(BRProject.created_by == current_user.id)
        brs = br_q.limit(page_size).all()
        results["br_projects"] = [
            {"id": str(b.id), "title": b.title, "status": b.status, "created_at": b.created_at.isoformat()}
            for b in brs
        ]

    if type in ("all", "proposal"):
        prop_q = db.query(Proposal).filter(
            Proposal.is_deleted == False,
            or_(
                Proposal.vendor_name.ilike(pattern),
                Proposal.extracted_text.ilike(pattern),
                Proposal.vendor_email.ilike(pattern),
            ),
        )
        props = prop_q.limit(page_size).all()
        results["proposals"] = [
            {
                "id": str(p.id),
                "vendor_name": p.vendor_name,
                "status": p.status,
                "overall_score": p.matching_result.overall_score if p.matching_result else None,
                "uploaded_at": p.uploaded_at.isoformat(),
            }
            for p in props
        ]

    results["total"] = len(results["br_projects"]) + len(results["proposals"])
    return ApiResponse(data=results)


@router.get("/proposals/{proposal_id}/match/filter", response_model=ApiResponse[list])
async def filter_requirement_matchings(
    proposal_id: uuid.UUID,
    label: str | None = Query(None, description="strong_match|partial_match|gap_identified|missing"),
    category: str | None = Query(None),
    min_score: float | None = Query(None, ge=0.0, le=1.0),
    max_score: float | None = Query(None, ge=0.0, le=1.0),
    sort_by: str = Query("score", regex="^(score|category|priority)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted:
        raise HTTPException(404, "Proposal not found")
    result = proposal.matching_result
    if not result:
        raise HTTPException(404, "Matching not completed")

    q = (
        db.query(RequirementMatching)
        .filter(RequirementMatching.result_id == result.id)
        .join(RequirementMatching.br_requirement)
    )

    if label:
        q = q.filter(RequirementMatching.label == label)
    if category:
        q = q.filter(BRRequirement.category == category)
    if min_score is not None:
        q = q.filter(RequirementMatching.score >= min_score)
    if max_score is not None:
        q = q.filter(RequirementMatching.score <= max_score)

    sort_col = {
        "score": RequirementMatching.score,
        "category": BRRequirement.category,
        "priority": BRRequirement.priority,
    }[sort_by]
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    matchings = q.all()

    return ApiResponse(data=[
        {
            "id": str(m.id),
            "br_requirement": m.br_requirement.text if m.br_requirement else "",
            "category": m.br_requirement.category if m.br_requirement else "",
            "priority": m.br_requirement.priority if m.br_requirement else "",
            "proposal_text": m.proposal_requirement.text if m.proposal_requirement else None,
            "score": m.score,
            "label": m.label,
            "explanation": m.explanation,
        }
        for m in matchings
    ])


@router.get("/br-projects/{br_id}/proposals/ranked", response_model=ApiResponse[list])
async def get_ranked_proposals(
    br_id: uuid.UUID,
    status: str | None = Query(None),
    min_score: float | None = Query(None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return proposals for a BR project sorted by overall match score descending."""
    q = (
        db.query(Proposal)
        .filter(Proposal.project_id == br_id, Proposal.is_deleted == False)
        .outerjoin(Proposal.matching_result)
    )
    if status:
        q = q.filter(Proposal.status == status)

    proposals = q.all()
    ranked = []
    for p in proposals:
        score = p.matching_result.overall_score if p.matching_result else None
        if min_score is not None and (score is None or score < min_score):
            continue
        ranked.append({
            "id": str(p.id),
            "vendor_name": p.vendor_name,
            "status": p.status,
            "overall_score": score,
            "proposed_cost": p.proposed_cost,
            "proposed_timeline_months": p.proposed_timeline_months,
        })

    ranked.sort(key=lambda x: x["overall_score"] or 0, reverse=True)
    return ApiResponse(data=ranked)
