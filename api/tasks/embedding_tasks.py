"""Celery tasks for batch embedding generation."""
import uuid
import logging
from .celery_app import celery_app
from ..database import SessionLocal
from ..models.br import BRRequirement
from ..models.proposal import ProposalRequirement

logger = logging.getLogger(__name__)


@celery_app.task(name="api.tasks.embedding_tasks.embed_br_requirements")
def embed_br_requirements_task(br_id: str):
    """Generate embeddings for all un-embedded BR requirements."""
    db = SessionLocal()
    try:
        reqs = (
            db.query(BRRequirement)
            .filter(
                BRRequirement.project_id == uuid.UUID(br_id),
                BRRequirement.embedding == None,
                BRRequirement.is_deleted == False,
            )
            .all()
        )
        if not reqs:
            return {"embedded": 0}

        from ..services.embedding_service import generate_embeddings
        texts = [r.text for r in reqs]
        embeddings = generate_embeddings(texts)
        for req, emb in zip(reqs, embeddings):
            req.embedding = emb
        db.commit()
        logger.info("Embedded %d BR requirements for project %s", len(reqs), br_id)
        return {"embedded": len(reqs)}
    finally:
        db.close()


@celery_app.task(name="api.tasks.embedding_tasks.embed_proposal_requirements")
def embed_proposal_requirements_task(proposal_id: str):
    """Generate embeddings for all un-embedded proposal requirements."""
    db = SessionLocal()
    try:
        reqs = (
            db.query(ProposalRequirement)
            .filter(
                ProposalRequirement.proposal_id == uuid.UUID(proposal_id),
                ProposalRequirement.embedding == None,
            )
            .all()
        )
        if not reqs:
            return {"embedded": 0}

        from ..services.embedding_service import generate_embeddings
        texts = [r.text for r in reqs]
        embeddings = generate_embeddings(texts)
        for req, emb in zip(reqs, embeddings):
            req.embedding = emb
        db.commit()
        logger.info("Embedded %d proposal requirements for %s", len(reqs), proposal_id)
        return {"embedded": len(reqs)}
    finally:
        db.close()
