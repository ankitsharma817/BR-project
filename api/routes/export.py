"""
Export endpoints — PDF and Excel reports for match results.
GET /api/v1/proposals/{id}/export?format=pdf|excel
GET /api/v1/proposals/compare/export?format=excel&ids=...
"""
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.proposal import Proposal
from ..models.matching import MatchingResult

router = APIRouter(tags=["export"])


def _get_proposal_and_result(proposal_id: uuid.UUID, db: Session):
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.is_deleted:
        raise HTTPException(404, "Proposal not found")
    result = proposal.matching_result
    if not result:
        raise HTTPException(404, "Matching result not available yet")
    return proposal, result


@router.get("/proposals/{proposal_id}/export")
async def export_proposal_report(
    proposal_id: uuid.UUID,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal, result = _get_proposal_and_result(proposal_id, db)
    analysis = result.analysis

    if format == "pdf":
        from ..services.export.pdf_export import generate_match_pdf
        content = generate_match_pdf(proposal, result, analysis)
        filename = f"match_report_{proposal.vendor_name.replace(' ', '_')}.pdf"
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Excel
    from ..services.export.excel_export import generate_match_excel
    content = generate_match_excel(proposal, result, analysis)
    filename = f"match_report_{proposal.vendor_name.replace(' ', '_')}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/proposals/compare/export")
async def export_comparison_report(
    ids: str = Query(..., description="Comma-separated proposal UUIDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal_ids = [uuid.UUID(i.strip()) for i in ids.split(",") if i.strip()]
    if len(proposal_ids) < 2:
        raise HTTPException(422, "Provide at least 2 proposal IDs")

    from ..services.matching_service import run_matching
    comparisons = []
    for pid in proposal_ids:
        proposal = db.get(Proposal, pid)
        if not proposal:
            continue
        entry: dict = {
            "proposal_id": str(pid),
            "vendor_name": proposal.vendor_name,
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
        comparisons.append(entry)

    from ..services.export.excel_export import generate_comparison_excel
    content = generate_comparison_excel(comparisons)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="comparison_report.xlsx"'},
    )
