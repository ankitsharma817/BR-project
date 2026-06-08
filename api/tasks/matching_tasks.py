"""Celery tasks for async matching pipeline."""
import uuid
import logging
from .celery_app import celery_app
from ..database import SessionLocal
from ..models.proposal import Proposal
from ..models.br import BRRequirement

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="api.tasks.matching_tasks.run_matching",
    max_retries=3,
    default_retry_delay=30,
)
def run_matching_task(self, proposal_id: str, triggered_by: str | None = None):
    """Full matching pipeline for a single proposal."""
    db = SessionLocal()
    try:
        proposal = db.get(Proposal, uuid.UUID(proposal_id))
        if not proposal:
            logger.error("Proposal %s not found", proposal_id)
            return {"status": "error", "detail": "Proposal not found"}

        proposal.status = "processing"
        db.commit()

        br_reqs = (
            db.query(BRRequirement)
            .filter(
                BRRequirement.project_id == proposal.project_id,
                BRRequirement.is_deleted == False,
            )
            .all()
        )

        if not br_reqs:
            proposal.status = "failed"
            db.commit()
            return {"status": "error", "detail": "No BR requirements found"}

        from ..services.matching_service import run_matching
        result = run_matching(
            db,
            proposal,
            br_reqs,
            triggered_by=uuid.UUID(triggered_by) if triggered_by else None,
        )

        # Fire webhook notification
        from .webhook_tasks import fire_event_task
        fire_event_task.delay(
            event="match.completed",
            payload={
                "proposal_id": proposal_id,
                "vendor_name": proposal.vendor_name,
                "overall_score": result.overall_score,
                "version": result.version,
            },
            project_id=str(proposal.project_id),
        )

        logger.info("Matching completed for proposal %s — score %.2f", proposal_id, result.overall_score)
        return {"status": "completed", "overall_score": result.overall_score}

    except Exception as exc:
        logger.exception("Matching failed for proposal %s", proposal_id)
        db_retry = SessionLocal()
        try:
            p = db_retry.get(Proposal, uuid.UUID(proposal_id))
            if p:
                p.status = "failed"
                db_retry.commit()
        finally:
            db_retry.close()
        raise self.retry(exc=exc)

    finally:
        db.close()


@celery_app.task(name="api.tasks.matching_tasks.recalculate_all_for_br")
def recalculate_all_for_br_task(br_id: str, triggered_by: str | None = None):
    """Recalculate matching for ALL proposals under a BR project."""
    db = SessionLocal()
    try:
        proposals = (
            db.query(Proposal)
            .filter(
                Proposal.project_id == uuid.UUID(br_id),
                Proposal.is_deleted == False,
                Proposal.status == "matched",
            )
            .all()
        )
        task_ids = []
        for p in proposals:
            task = run_matching_task.delay(str(p.id), triggered_by)
            task_ids.append({"proposal_id": str(p.id), "task_id": task.id})
        return {"queued": len(task_ids), "tasks": task_ids}
    finally:
        db.close()
