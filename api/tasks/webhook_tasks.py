"""Celery task: fire webhook deliveries with HMAC signature."""
import hashlib
import hmac
import json
import logging
import uuid
import httpx
from .celery_app import celery_app
from ..database import SessionLocal
from ..models.webhook import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)

SUPPORTED_EVENTS = {
    "match.completed",
    "proposal.uploaded",
    "proposal.failed",
    "br.created",
    "br.deleted",
    "score.threshold_crossed",
}


def _sign_payload(secret: str, payload: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


@celery_app.task(
    bind=True,
    name="api.tasks.webhook_tasks.fire_event",
    max_retries=3,
    default_retry_delay=60,
)
def fire_event_task(self, event: str, payload: dict, project_id: str | None = None):
    """Deliver a webhook event to all registered subscribers."""
    db = SessionLocal()
    try:
        q = db.query(Webhook).filter(Webhook.is_active == True)
        if project_id:
            from sqlalchemy import or_
            q = q.filter(
                or_(
                    Webhook.project_id == uuid.UUID(project_id),
                    Webhook.project_id == None,
                )
            )
        hooks = q.all()

        body = json.dumps({"event": event, "data": payload}, default=str).encode()

        for hook in hooks:
            if event not in (hook.events or []):
                continue
            signature = _sign_payload(hook.secret, body)
            headers = {
                "Content-Type": "application/json",
                "X-BRMatch-Event": event,
                "X-BRMatch-Signature": signature,
            }
            delivery = WebhookDelivery(webhook_id=hook.id, event=event, payload=payload)
            try:
                resp = httpx.post(hook.url, content=body, headers=headers, timeout=10)
                delivery.status_code = resp.status_code
                delivery.response_body = resp.text[:500]
                delivery.success = resp.status_code < 400
                logger.info("Webhook %s → %s: %d", event, hook.url, resp.status_code)
            except Exception as exc:
                delivery.success = False
                delivery.response_body = str(exc)[:500]
                logger.warning("Webhook delivery failed for %s: %s", hook.url, exc)
            db.add(delivery)

        db.commit()
    finally:
        db.close()
