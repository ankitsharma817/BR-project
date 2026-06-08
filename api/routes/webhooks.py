"""
Webhook management endpoints.
POST   /api/v1/webhooks
GET    /api/v1/webhooks
GET    /api/v1/webhooks/{id}
PUT    /api/v1/webhooks/{id}
DELETE /api/v1/webhooks/{id}
GET    /api/v1/webhooks/{id}/deliveries
POST   /api/v1/webhooks/{id}/test
"""
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.webhook import Webhook, WebhookDelivery
from ..schemas.common import ApiResponse, MessageResponse
from ..tasks.webhook_tasks import SUPPORTED_EVENTS

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    url: str
    events: list[str]
    project_id: uuid.UUID | None = None

    def validate_events(self):
        bad = [e for e in self.events if e not in SUPPORTED_EVENTS]
        if bad:
            raise HTTPException(422, f"Unknown events: {bad}. Supported: {sorted(SUPPORTED_EVENTS)}")


class WebhookUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    id: uuid.UUID
    url: str
    events: list[str]
    is_active: bool
    project_id: uuid.UUID | None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data.validate_events()
    secret = secrets.token_hex(32)
    hook = Webhook(
        owner_id=current_user.id,
        url=data.url,
        secret=secret,
        events=data.events,
        project_id=data.project_id,
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return ApiResponse(
        data={"id": str(hook.id), "secret": secret, "url": hook.url, "events": hook.events},
        message="Webhook created. Save the secret — it will not be shown again.",
    )


@router.get("", response_model=ApiResponse[list])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hooks = db.query(Webhook).filter(Webhook.owner_id == current_user.id).all()
    return ApiResponse(data=[
        {"id": str(h.id), "url": h.url, "events": h.events, "is_active": h.is_active,
         "project_id": str(h.project_id) if h.project_id else None}
        for h in hooks
    ])


@router.get("/{hook_id}", response_model=ApiResponse[dict])
async def get_webhook(
    hook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hook = db.get(Webhook, hook_id)
    if not hook or str(hook.owner_id) != str(current_user.id):
        raise HTTPException(404, "Webhook not found")
    return ApiResponse(data={
        "id": str(hook.id), "url": hook.url, "events": hook.events,
        "is_active": hook.is_active, "project_id": str(hook.project_id) if hook.project_id else None,
        "created_at": hook.created_at.isoformat(),
    })


@router.put("/{hook_id}", response_model=ApiResponse[dict])
async def update_webhook(
    hook_id: uuid.UUID,
    data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hook = db.get(Webhook, hook_id)
    if not hook or str(hook.owner_id) != str(current_user.id):
        raise HTTPException(404, "Webhook not found")
    if data.url is not None:
        hook.url = data.url
    if data.events is not None:
        bad = [e for e in data.events if e not in SUPPORTED_EVENTS]
        if bad:
            raise HTTPException(422, f"Unknown events: {bad}")
        hook.events = data.events
    if data.is_active is not None:
        hook.is_active = data.is_active
    db.commit()
    return ApiResponse(data={"id": str(hook.id), "is_active": hook.is_active})


@router.delete("/{hook_id}", response_model=MessageResponse)
async def delete_webhook(
    hook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hook = db.get(Webhook, hook_id)
    if not hook or str(hook.owner_id) != str(current_user.id):
        raise HTTPException(404, "Webhook not found")
    db.delete(hook)
    db.commit()
    return MessageResponse(message="Webhook deleted")


@router.get("/{hook_id}/deliveries", response_model=ApiResponse[list])
async def get_deliveries(
    hook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hook = db.get(Webhook, hook_id)
    if not hook or str(hook.owner_id) != str(current_user.id):
        raise HTTPException(404, "Webhook not found")
    deliveries = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.webhook_id == hook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(50)
        .all()
    )
    return ApiResponse(data=[
        {
            "id": str(d.id),
            "event": d.event,
            "success": d.success,
            "status_code": d.status_code,
            "attempt": d.attempt,
            "delivered_at": d.delivered_at.isoformat(),
        }
        for d in deliveries
    ])


@router.post("/{hook_id}/test", response_model=ApiResponse[dict])
async def test_webhook(
    hook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hook = db.get(Webhook, hook_id)
    if not hook or str(hook.owner_id) != str(current_user.id):
        raise HTTPException(404, "Webhook not found")
    from ..tasks.webhook_tasks import fire_event_task
    task = fire_event_task.delay(
        event="match.completed",
        payload={"test": True, "webhook_id": str(hook_id), "message": "This is a test delivery"},
    )
    return ApiResponse(data={"task_id": task.id, "message": "Test delivery queued"})
