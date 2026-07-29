from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.middleware import client_ip_from_request
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.ip_block import (
    IpBlockCreate,
    IpBlockRead,
    IpBlockSummary,
    IpBlockUnblock,
)
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.ip_block_service import (
    IpBlockError,
    create_ip_block,
    ip_block_summary,
    list_ip_blocks,
    normalize_ip_address,
    unblock_ip_block,
)

router = APIRouter(prefix="/ip-blocks", tags=["admin-security"])


@router.get("", response_model=list[IpBlockRead])
def admin_list_ip_blocks(
    status_filter: str = Query(
        default="active",
        alias="status",
        pattern="^(active|expired|unblocked|all)$",
    ),
    search: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[IpBlockRead]:
    try:
        return list_ip_blocks(db, status=status_filter, search=search, limit=limit)
    except IpBlockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/summary", response_model=IpBlockSummary)
def admin_ip_block_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> IpBlockSummary:
    return ip_block_summary(db)


def _normalized_request_ip(request: Request) -> str | None:
    request_ip = client_ip_from_request(request)
    if not request_ip:
        return None
    try:
        return normalize_ip_address(request_ip)
    except IpBlockError:
        return None


@router.post("", response_model=IpBlockRead, status_code=status.HTTP_201_CREATED)
def admin_create_ip_block(
    payload: IpBlockCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> IpBlockRead:
    try:
        if _normalized_request_ip(request) == normalize_ip_address(payload.ip_address):
            raise IpBlockError("You cannot block the IP address used by your current staff session.")
        row = create_ip_block(db, actor=current_user, payload=payload)
    except IpBlockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="ip_block",
        entity_id=row.id,
        action="create",
        summary=f"IP address blocked: {row.reason}",
        changed_fields=["ip_address", "reason", "expires_at"],
    )
    return row


@router.post("/{block_id}/unblock", response_model=IpBlockRead)
def admin_unblock_ip(
    block_id: int,
    payload: IpBlockUnblock,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> IpBlockRead:
    try:
        row = unblock_ip_block(db, block_id=block_id, actor=current_user, reason=payload.reason)
    except IpBlockError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="ip_block",
        entity_id=row.id,
        action="update",
        summary="IP address unblocked.",
        changed_fields=["unblocked_at", "unblock_reason"],
    )
    return row
