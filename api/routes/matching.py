import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.proposal import Proposal
from ..models.br import BRRequirement
from ..models.matching import MatchingResult, RequirementMatching, MatchHistory
from ..schemas.matching import MatchingResultResponse, RequirementMatchingResponse, MatchAnalysisResponse, CompareRequest, RiskItem, RecommendationItem
from ..schemas.common import ApiResponse, MessageResponse
from ..services.matching_service import run_matching

router = APIRouter(prefix="/proposals", tags=["matching"])


def _build_result_response(result: MatchingResult) -> MatchingResultResponse:
    matchings = []
    for rm in result.requirement_matchings:
        br_req = rm.br_requirement
        prop_req = rm.proposal_requirement
        matchings.append(RequirementMatchingResponse(
            id=rm.id,
            br_requirement_text=br_req.text if br_req else "",
            br_requirement_category=br_req.category if br_req else "",
            br_requirement_priority=br_req.priority if br_req else "",
            proposal_requirement_text=prop_req.text if prop_req else None,
            score=rm.score,
            label=rm.label,
            explanation=rm.explanation,
        ))
    resp = MatchingResultResponse.model_validate(result)
    resp.requirement_matchings = matchings
    return resp


@router.get("/{proposal_id}/match", response_model=ApiResponse[MatchingResultResponse])
async def get_match_result(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted:
        raise HTTPException(404, "Proposal not found")
    result = proposal.matching_result
    if not result:
        raise HTTPException(404, "Matching not yet completed")
    return ApiResponse(data=_build_result_response(result))


@router.get("/{proposal_id}/analysis", response_model=ApiResponse[MatchAnalysisResponse])
async def get_analysis(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted:
        raise HTTPException(404, "Proposal not found")
    result = proposal.matching_result
    if not result or not result.analysis:
        raise HTTPException(404, "Analysis not available yet")
    a = result.analysis
    return ApiResponse(data=MatchAnalysisResponse(
        result_id=result.id,
        risks=[RiskItem(**r) for r in (a.risks or [])],
        recommendations=[RecommendationItem(**r) for r in (a.recommendations or [])],
        strengths=a.strengths or [],
        gaps=a.gaps or [],
    ))


@router.post("/{proposal_id}/recalculate", response_model=ApiResponse[dict])
async def recalculate_match(
    proposal_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted:
        raise HTTPException(404, "Proposal not found")

    proposal.status = "processing"
    db.commit()

    from ..database import SessionLocal

    def _recalc(pid, uid, factory):
        _db = factory()
        try:
            p = _db.get(Proposal, pid)
            br_reqs = _db.query(BRRequirement).filter(
                BRRequirement.project_id == p.project_id,
                BRRequirement.is_deleted == False,
            ).all()
            run_matching(_db, p, br_reqs, triggered_by=uid)
        finally:
            _db.close()

    background_tasks.add_task(_recalc, proposal_id, current_user.id, SessionLocal)
    return ApiResponse(data={"status": "recalculation_started"}, message="Recalculation queued")


@router.get("/{proposal_id}/history", response_model=ApiResponse[list[dict]])
async def get_match_history(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted:
        raise HTTPException(404, "Proposal not found")
    result = proposal.matching_result
    if not result:
        return ApiResponse(data=[])
    history = (
        db.query(MatchHistory)
        .filter(MatchHistory.result_id == result.id)
        .order_by(MatchHistory.recalculated_at.desc())
        .all()
    )
    return ApiResponse(data=[
        {
            "version": h.version,
            "overall_score": h.overall_score,
            "scores_snapshot": h.scores_snapshot,
            "recalculated_at": h.recalculated_at.isoformat(),
        }
        for h in history
    ])


@router.post("/compare", response_model=ApiResponse[list[dict]])
async def compare_proposals(
    body: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = []
    for pid in body.proposal_ids:
        proposal = db.get(Proposal, pid)
        if not proposal:
            continue
        entry = {
            "proposal_id": str(pid),
            "vendor_name": proposal.vendor_name,
            "status": proposal.status,
            "overall_score": None,
            "category_scores": {},
        }
        if proposal.matching_result:
            r = proposal.matching_result
            entry["overall_score"] = r.overall_score
            entry["category_scores"] = {
                "functional": r.functional_score,
                "technical": r.technical_score,
                "compliance": r.compliance_score,
                "security": r.security_score,
                "timeline": r.timeline_score,
                "resource": r.resource_score,
                "deliverables": r.deliverables_score,
            }
        results.append(entry)

    results.sort(key=lambda x: x["overall_score"] or 0, reverse=True)
    return ApiResponse(data=results)
