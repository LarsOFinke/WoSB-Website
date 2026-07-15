from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.outbound_webhook import (
    OutboundWebhookCreate,
    OutboundWebhookDeliveryRead,
    OutboundWebhookEventCatalogItem,
    OutboundWebhookRead,
    OutboundWebhookSummary,
    OutboundWebhookTestRequest,
    OutboundWebhookUpdate,
)
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.outbound_webhook_delivery_service import (
    create_test_delivery,
    retry_delivery,
)
from app.modules.admin.services.outbound_webhook_service import (
    OutboundWebhookError,
    create_webhook,
    delete_webhook,
    event_catalog,
    list_deliveries,
    list_webhooks,
    rotate_webhook_secret,
    update_webhook,
    webhook_summary,
)

router = APIRouter(prefix="/integrations/webhooks", tags=["admin-integrations"])


def _bad_request(exc: OutboundWebhookError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/events", response_model=list[OutboundWebhookEventCatalogItem])
def admin_webhook_event_catalog(
    _: User = Depends(require_admin),
) -> list[OutboundWebhookEventCatalogItem]:
    return event_catalog()


@router.get("/summary", response_model=OutboundWebhookSummary)
def admin_webhook_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> OutboundWebhookSummary:
    return webhook_summary(db)


@router.get("", response_model=list[OutboundWebhookRead])
def admin_list_webhooks(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[OutboundWebhookRead]:
    return list_webhooks(db)


@router.post("", response_model=OutboundWebhookRead, status_code=status.HTTP_201_CREATED)
def admin_create_webhook(
    payload: OutboundWebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OutboundWebhookRead:
    try:
        row = create_webhook(db, payload, current_user)
    except OutboundWebhookError as exc:
        raise _bad_request(exc) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="outbound_webhook",
        entity_id=row.id,
        action="create",
        summary=f'Outbound webhook “{row.name}” created.',
        changed_fields=["endpoint_url", "event_types", "delivery_mode", "scope_type", "scope_id", "message_template", "is_active"],
    )
    return row


@router.put("/{webhook_id}", response_model=OutboundWebhookRead)
def admin_update_webhook(
    webhook_id: int,
    payload: OutboundWebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OutboundWebhookRead:
    try:
        row = update_webhook(db, webhook_id, payload)
    except OutboundWebhookError as exc:
        raise _bad_request(exc) from exc
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="outbound_webhook",
        entity_id=row.id,
        action="update",
        summary=f'Outbound webhook “{row.name}” updated.',
        changed_fields=["endpoint_url", "event_types", "delivery_mode", "scope_type", "scope_id", "message_template", "is_active"],
    )
    return row


@router.post("/{webhook_id}/rotate-secret", response_model=OutboundWebhookRead)
def admin_rotate_webhook_secret(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OutboundWebhookRead:
    try:
        row = rotate_webhook_secret(db, webhook_id)
    except OutboundWebhookError as exc:
        raise _bad_request(exc) from exc
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="outbound_webhook",
        entity_id=row.id,
        action="update",
        summary=f'Signing secret for outbound webhook “{row.name}” rotated.',
        changed_fields=["signing_secret"],
    )
    return row


@router.post("/{webhook_id}/test", response_model=OutboundWebhookDeliveryRead)
def admin_test_webhook(
    webhook_id: int,
    payload: OutboundWebhookTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OutboundWebhookDeliveryRead:
    row = create_test_delivery(db, webhook_id, current_user, payload.event_type)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found.")
    return row


@router.get("/deliveries/history", response_model=list[OutboundWebhookDeliveryRead])
def admin_list_webhook_deliveries(
    webhook_id: int | None = Query(default=None, ge=1),
    delivery_status: str | None = Query(default=None, alias="status", pattern="^(queued|success|failed)$"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[OutboundWebhookDeliveryRead]:
    return list_deliveries(db, webhook_id=webhook_id, status=delivery_status, limit=limit)


@router.post("/deliveries/{delivery_id}/retry", response_model=OutboundWebhookDeliveryRead)
def admin_retry_webhook_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> OutboundWebhookDeliveryRead:
    row = retry_delivery(db, delivery_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found.")
    return row


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    if not delete_webhook(db, webhook_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="outbound_webhook",
        entity_id=webhook_id,
        action="delete",
        summary=f"Outbound webhook #{webhook_id} deleted.",
    )
