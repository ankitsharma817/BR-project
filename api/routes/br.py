import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.br import BRProject, BRDocument, BRRequirement
from ..schemas.br import BRCreate, BRUpdate, BRResponse, BRDetailResponse, RequirementCreate, RequirementUpdate, RequirementResponse
from ..schemas.common import ApiResponse, PaginatedResponse, MessageResponse
from ..services import file_service
from ..services.matching_service import extract_requirements
from ..utils.validators import validate_upload_file, validate_pagination

router = APIRouter(prefix="/br-projects", tags=["br-projects"])


def _br_response(br: BRProject) -> BRResponse:
    req_count = sum(1 for r in br.requirements if not r.is_deleted)
    prop_count = sum(1 for p in br.proposals if not p.is_deleted)
    d = BRResponse.model_validate(br)
    d.requirement_count = req_count
    d.proposal_count = prop_count
    return d


@router.post("", response_model=ApiResponse[BRResponse], status_code=201)
async def create_br(
    data: BRCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    br = BRProject(**data.model_dump(), created_by=current_user.id)
    db.add(br)
    db.commit()
    db.refresh(br)
    return ApiResponse(data=_br_response(br), message="BR project created")


@router.get("", response_model=PaginatedResponse[BRResponse])
async def list_brs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_pagination(page, page_size)
    q = db.query(BRProject).filter(BRProject.is_deleted == False)
    if current_user.role != "admin":
        q = q.filter(BRProject.created_by == current_user.id)
    if status:
        q = q.filter(BRProject.status == status)
    total = q.count()
    items = q.order_by(BRProject.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_br_response(b) for b in items],
        total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{br_id}", response_model=ApiResponse[BRDetailResponse])
async def get_br(
    br_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    br = db.get(BRProject, br_id)
    if not br or br.is_deleted:
        from fastapi import HTTPException
        raise HTTPException(404, "BR project not found")
    detail = BRDetailResponse.model_validate(br)
    detail.requirements = [RequirementResponse.model_validate(r) for r in br.requirements if not r.is_deleted]
    detail.requirement_count = len(detail.requirements)
    detail.proposal_count = sum(1 for p in br.proposals if not p.is_deleted)
    return ApiResponse(data=detail)


@router.put("/{br_id}", response_model=ApiResponse[BRResponse])
async def update_br(
    br_id: uuid.UUID,
    data: BRUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    br = db.get(BRProject, br_id)
    if not br or br.is_deleted:
        from fastapi import HTTPException
        raise HTTPException(404, "BR project not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(br, field, value)
    db.commit()
    db.refresh(br)
    return ApiResponse(data=_br_response(br), message="BR project updated")


@router.delete("/{br_id}", response_model=MessageResponse)
async def delete_br(
    br_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    br = db.get(BRProject, br_id)
    if not br or br.is_deleted:
        from fastapi import HTTPException
        raise HTTPException(404, "BR project not found")
    br.is_deleted = True
    db.commit()
    return MessageResponse(message="BR project deleted")


@router.post("/{br_id}/documents", response_model=ApiResponse[dict], status_code=201)
async def upload_br_document(
    br_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    await validate_upload_file(file)
    br = db.get(BRProject, br_id)
    if not br or br.is_deleted:
        from fastapi import HTTPException
        raise HTTPException(404, "BR project not found")

    saved = await file_service.save_upload(file, subfolder=f"br/{br_id}")
    text = file_service.extract_text(saved["content"], file.filename or "")

    doc = BRDocument(
        project_id=br_id,
        filename=file.filename or "upload",
        file_path=saved["file_path"],
        file_hash=saved["file_hash"],
        file_size=saved["file_size"],
        mime_type=saved["mime_type"],
        extracted_text=text,
        upload_status="completed",
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.flush()

    # Auto-extract requirements
    reqs = extract_requirements(text)
    for r in reqs:
        br_req = BRRequirement(project_id=br_id, source="extracted", **r)
        db.add(br_req)

    db.commit()
    return ApiResponse(
        data={"document_id": str(doc.id), "requirements_extracted": len(reqs)},
        message=f"Document uploaded. {len(reqs)} requirements extracted.",
    )


@router.get("/{br_id}/requirements", response_model=ApiResponse[list[RequirementResponse]])
async def list_requirements(
    br_id: uuid.UUID,
    category: str | None = Query(None),
    priority: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(BRRequirement).filter(
        BRRequirement.project_id == br_id,
        BRRequirement.is_deleted == False,
    )
    if category:
        q = q.filter(BRRequirement.category == category)
    if priority:
        q = q.filter(BRRequirement.priority == priority)
    reqs = q.all()
    return ApiResponse(data=[RequirementResponse.model_validate(r) for r in reqs])


@router.post("/{br_id}/requirements", response_model=ApiResponse[RequirementResponse], status_code=201)
async def create_requirement(
    br_id: uuid.UUID,
    data: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = BRRequirement(project_id=br_id, source="manual", **data.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    return ApiResponse(data=RequirementResponse.model_validate(req), message="Requirement created", status_code=201)


@router.put("/{br_id}/requirements/{req_id}", response_model=ApiResponse[RequirementResponse])
async def update_requirement(
    br_id: uuid.UUID,
    req_id: uuid.UUID,
    data: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.get(BRRequirement, req_id)
    if not req or req.is_deleted or str(req.project_id) != str(br_id):
        from fastapi import HTTPException
        raise HTTPException(404, "Requirement not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(req, field, value)
    req.embedding = None  # invalidate embedding on text change
    db.commit()
    db.refresh(req)
    return ApiResponse(data=RequirementResponse.model_validate(req))


@router.delete("/{br_id}/requirements/{req_id}", response_model=MessageResponse)
async def delete_requirement(
    br_id: uuid.UUID,
    req_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.get(BRRequirement, req_id)
    if not req or req.is_deleted or str(req.project_id) != str(br_id):
        from fastapi import HTTPException
        raise HTTPException(404, "Requirement not found")
    req.is_deleted = True
    db.commit()
    return MessageResponse(message="Requirement deleted")
