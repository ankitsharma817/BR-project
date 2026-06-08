import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.br import BRProject, BRRequirement
from ..models.proposal import Proposal, ProposalRequirement
from ..schemas.proposal import ProposalCreate, ProposalResponse, ProposalDetailResponse
from ..schemas.common import ApiResponse, PaginatedResponse, MessageResponse
from ..services import file_service
from ..services.matching_service import extract_requirements, run_matching
from ..utils.validators import validate_upload_file, validate_pagination

router = APIRouter(prefix="/br-projects", tags=["proposals"])


def _run_matching_bg(proposal_id: uuid.UUID, db_factory):
    db: Session = db_factory()
    try:
        proposal = db.get(Proposal, proposal_id)
        if not proposal:
            return
        br_reqs = (
            db.query(BRRequirement)
            .filter(BRRequirement.project_id == proposal.project_id, BRRequirement.is_deleted == False)
            .all()
        )
        run_matching(db, proposal, br_reqs)
    except Exception as e:
        proposal = db.get(Proposal, proposal_id)
        if proposal:
            proposal.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/{br_id}/proposals", response_model=ApiResponse[ProposalResponse], status_code=201)
async def upload_proposal(
    br_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    vendor_name: str = Query(...),
    vendor_contact: str | None = Query(None),
    vendor_email: str | None = Query(None),
    proposed_cost: float | None = Query(None),
    proposed_timeline_months: int | None = Query(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await validate_upload_file(file)
    br = db.get(BRProject, br_id)
    if not br or br.is_deleted:
        raise HTTPException(404, "BR project not found")

    saved = await file_service.save_upload(file, subfolder=f"proposals/{br_id}")
    text = file_service.extract_text(saved["content"], file.filename or "")

    proposal = Proposal(
        project_id=br_id,
        vendor_name=vendor_name,
        vendor_contact=vendor_contact,
        vendor_email=vendor_email,
        filename=file.filename or "upload",
        file_path=saved["file_path"],
        file_hash=saved["file_hash"],
        file_size=saved["file_size"],
        extracted_text=text,
        proposed_cost=proposed_cost,
        proposed_timeline_months=proposed_timeline_months,
        status="processing",
        uploaded_by=current_user.id,
    )
    db.add(proposal)
    db.flush()

    reqs = extract_requirements(text)
    for r in reqs:
        pr = ProposalRequirement(proposal_id=proposal.id, **r)
        db.add(pr)

    db.commit()
    db.refresh(proposal)

    from ..database import SessionLocal
    background_tasks.add_task(_run_matching_bg, proposal.id, SessionLocal)

    resp = ProposalResponse.model_validate(proposal)
    return ApiResponse(data=resp, message="Proposal uploaded. Matching started in background.")


@router.get("/{br_id}/proposals", response_model=PaginatedResponse[ProposalResponse])
async def list_proposals(
    br_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_pagination(page, page_size)
    q = db.query(Proposal).filter(Proposal.project_id == br_id, Proposal.is_deleted == False)
    if status:
        q = q.filter(Proposal.status == status)
    total = q.count()
    items = q.order_by(Proposal.uploaded_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for p in items:
        resp = ProposalResponse.model_validate(p)
        if p.matching_result:
            resp.overall_score = p.matching_result.overall_score
        results.append(resp)

    return PaginatedResponse(
        items=results, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{br_id}/proposals/{proposal_id}", response_model=ApiResponse[ProposalDetailResponse])
async def get_proposal(
    br_id: uuid.UUID,
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted or str(proposal.project_id) != str(br_id):
        raise HTTPException(404, "Proposal not found")
    detail = ProposalDetailResponse.model_validate(proposal)
    detail.requirement_count = len(proposal.requirements)
    if proposal.matching_result:
        detail.overall_score = proposal.matching_result.overall_score
    return ApiResponse(data=detail)


@router.delete("/{br_id}/proposals/{proposal_id}", response_model=MessageResponse)
async def delete_proposal(
    br_id: uuid.UUID,
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted or str(proposal.project_id) != str(br_id):
        raise HTTPException(404, "Proposal not found")
    proposal.is_deleted = True
    db.commit()
    return MessageResponse(message="Proposal deleted")


@router.get("/proposals/{proposal_id}/upload-status", response_model=ApiResponse[dict])
async def upload_status(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(404, "Proposal not found")
    return ApiResponse(data={"proposal_id": str(proposal_id), "status": proposal.status})
