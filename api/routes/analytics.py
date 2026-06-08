"""
Analytics & reporting endpoints.
GET /api/v1/analytics/overview
GET /api/v1/analytics/br/{id}/summary
GET /api/v1/analytics/score-distribution
GET /api/v1/analytics/vendor-performance
"""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.br import BRProject, BRRequirement
from ..models.proposal import Proposal
from ..models.matching import MatchingResult, RequirementMatching
from ..models.feedback import Feedback
from ..schemas.common import ApiResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=ApiResponse[dict])
async def analytics_overview(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Proposals created over time (daily buckets)
    proposals_over_time = (
        db.query(
            func.date_trunc("day", Proposal.uploaded_at).label("day"),
            func.count(Proposal.id).label("count"),
        )
        .filter(Proposal.uploaded_at >= since, Proposal.is_deleted == False)
        .group_by("day")
        .order_by("day")
        .all()
    )

    # Average score trend (weekly)
    score_trend = (
        db.query(
            func.date_trunc("week", MatchingResult.calculated_at).label("week"),
            func.avg(MatchingResult.overall_score).label("avg_score"),
            func.count(MatchingResult.id).label("count"),
        )
        .filter(MatchingResult.calculated_at >= since)
        .group_by("week")
        .order_by("week")
        .all()
    )

    # Category avg scores across all results
    cat_avgs = db.query(
        func.avg(MatchingResult.functional_score).label("functional"),
        func.avg(MatchingResult.technical_score).label("technical"),
        func.avg(MatchingResult.compliance_score).label("compliance"),
        func.avg(MatchingResult.security_score).label("security"),
        func.avg(MatchingResult.timeline_score).label("timeline"),
        func.avg(MatchingResult.resource_score).label("resource"),
        func.avg(MatchingResult.deliverables_score).label("deliverables"),
    ).one()

    return ApiResponse(data={
        "period_days": days,
        "proposals_over_time": [
            {"day": str(r.day)[:10], "count": r.count}
            for r in proposals_over_time
        ],
        "score_trend": [
            {"week": str(r.week)[:10], "avg_score": round(float(r.avg_score), 4), "count": r.count}
            for r in score_trend
        ],
        "category_averages": {
            col: round(float(getattr(cat_avgs, col)), 4) if getattr(cat_avgs, col) is not None else None
            for col in ["functional", "technical", "compliance", "security", "timeline", "resource", "deliverables"]
        },
    })


@router.get("/br/{br_id}/summary", response_model=ApiResponse[dict])
async def br_analytics_summary(
    br_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    br = db.get(BRProject, br_id)
    if not br or br.is_deleted:
        raise HTTPException(404, "BR project not found")

    proposals = (
        db.query(Proposal)
        .filter(Proposal.project_id == br_id, Proposal.is_deleted == False)
        .all()
    )
    total = len(proposals)
    matched = sum(1 for p in proposals if p.status == "matched")
    scores = [p.matching_result.overall_score for p in proposals if p.matching_result]

    # Requirement coverage: how many reqs got ≥ 80% in any proposal
    req_count = db.query(BRRequirement).filter(
        BRRequirement.project_id == br_id, BRRequirement.is_deleted == False
    ).count()

    well_covered = (
        db.query(func.count(func.distinct(RequirementMatching.br_requirement_id)))
        .join(MatchingResult)
        .join(Proposal)
        .filter(
            Proposal.project_id == br_id,
            RequirementMatching.score >= 0.8,
        )
        .scalar()
    ) or 0

    # Best proposal
    best = max(proposals, key=lambda p: (p.matching_result.overall_score if p.matching_result else 0), default=None)

    return ApiResponse(data={
        "br_id": str(br_id),
        "title": br.title,
        "total_proposals": total,
        "matched_proposals": matched,
        "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
        "max_score": round(max(scores), 4) if scores else None,
        "min_score": round(min(scores), 4) if scores else None,
        "total_requirements": req_count,
        "well_covered_requirements": well_covered,
        "coverage_rate": round(well_covered / req_count, 4) if req_count else None,
        "best_vendor": {
            "id": str(best.id),
            "name": best.vendor_name,
            "score": best.matching_result.overall_score if best and best.matching_result else None,
        } if best else None,
    })


@router.get("/score-distribution", response_model=ApiResponse[dict])
async def score_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Histogram of overall scores across all matched proposals."""
    buckets = {
        "0-20%": (0.0, 0.2),
        "20-40%": (0.2, 0.4),
        "40-60%": (0.4, 0.6),
        "60-80%": (0.6, 0.8),
        "80-100%": (0.8, 1.01),
    }
    distribution = {}
    for label, (low, high) in buckets.items():
        count = (
            db.query(func.count(MatchingResult.id))
            .filter(
                MatchingResult.overall_score >= low,
                MatchingResult.overall_score < high,
            )
            .scalar()
        ) or 0
        distribution[label] = count

    label_counts = (
        db.query(RequirementMatching.label, func.count(RequirementMatching.id))
        .group_by(RequirementMatching.label)
        .all()
    )

    return ApiResponse(data={
        "overall_score_distribution": distribution,
        "requirement_label_counts": {label: count for label, count in label_counts},
    })


@router.get("/vendor-performance", response_model=ApiResponse[list])
async def vendor_performance(
    min_proposals: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate vendor performance across all BR projects."""
    results = (
        db.query(
            Proposal.vendor_name,
            func.count(Proposal.id).label("proposal_count"),
            func.avg(MatchingResult.overall_score).label("avg_score"),
            func.max(MatchingResult.overall_score).label("best_score"),
            func.min(MatchingResult.overall_score).label("worst_score"),
        )
        .join(MatchingResult, Proposal.id == MatchingResult.proposal_id)
        .filter(Proposal.is_deleted == False)
        .group_by(Proposal.vendor_name)
        .having(func.count(Proposal.id) >= min_proposals)
        .order_by(func.avg(MatchingResult.overall_score).desc())
        .all()
    )

    return ApiResponse(data=[
        {
            "vendor_name": r.vendor_name,
            "proposal_count": r.proposal_count,
            "avg_score": round(float(r.avg_score), 4),
            "best_score": round(float(r.best_score), 4),
            "worst_score": round(float(r.worst_score), 4),
        }
        for r in results
    ])
