from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, ip_address

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.modules.accounts.models.user import User
from app.modules.admin.models.ip_block import IpBlock
from app.modules.admin.schemas.ip_block import IpBlockCreate, IpBlockRead, IpBlockSummary


class IpBlockError(ValueError):
    pass


def normalize_ip_address(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        parsed = ip_address(raw)
    except ValueError as exc:
        raise IpBlockError("Enter a valid individual IPv4 or IPv6 address.") from exc
    if isinstance(parsed, IPv6Address) and parsed.ipv4_mapped:
        parsed = parsed.ipv4_mapped
    return parsed.compressed


def validate_blockable_ip(value: str) -> str:
    normalized = normalize_ip_address(value)
    if normalized is None:
        raise IpBlockError("Enter an IP address.")
    parsed: IPv4Address | IPv6Address = ip_address(normalized)
    if parsed.is_loopback or parsed.is_unspecified or parsed.is_multicast:
        raise IpBlockError("Loopback, unspecified and multicast addresses cannot be blocked.")
    return normalized


def _is_active(row: IpBlock, now: datetime | None = None) -> bool:
    now = now or utc_now()
    return row.unblocked_at is None and (row.expires_at is None or row.expires_at > now)


def to_read(row: IpBlock, now: datetime | None = None) -> IpBlockRead:
    now = now or utc_now()
    expired = row.unblocked_at is None and row.expires_at is not None and row.expires_at <= now
    return IpBlockRead(
        id=row.id,
        ip_address=row.ip_address,
        reason=row.reason,
        notes=row.notes,
        created_at=row.created_at,
        created_by_user_id=row.created_by_user_id,
        created_by_username=row.created_by_username,
        expires_at=row.expires_at,
        unblocked_at=row.unblocked_at,
        unblocked_by_user_id=row.unblocked_by_user_id,
        unblocked_by_username=row.unblocked_by_username,
        unblock_reason=row.unblock_reason,
        is_active=_is_active(row, now),
        is_temporary=row.expires_at is not None,
        is_expired=expired,
    )


def find_active_ip_block(db: Session, value: str | None) -> IpBlock | None:
    try:
        normalized = normalize_ip_address(value)
    except IpBlockError:
        return None
    if normalized is None:
        return None
    now = utc_now()
    return db.scalar(
        select(IpBlock)
        .where(
            IpBlock.ip_address == normalized,
            IpBlock.unblocked_at.is_(None),
            or_(IpBlock.expires_at.is_(None), IpBlock.expires_at > now),
        )
        .order_by(IpBlock.created_at.desc(), IpBlock.id.desc())
        .limit(1)
    )


def create_ip_block(db: Session, *, actor: User, payload: IpBlockCreate) -> IpBlockRead:
    normalized = validate_blockable_ip(payload.ip_address)
    if len(payload.reason.strip()) < 3:
        raise IpBlockError("Enter a reason with at least three characters.")
    now = utc_now()
    if payload.expires_at is not None and payload.expires_at <= now:
        raise IpBlockError("Expiration must be in the future.")
    if find_active_ip_block(db, normalized) is not None:
        raise IpBlockError("This IP address is already blocked.")
    row = IpBlock(
        ip_address=normalized,
        reason=payload.reason.strip(),
        notes=payload.notes,
        created_by_user_id=actor.id,
        created_by_username=actor.username,
        expires_at=payload.expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return to_read(row)


def unblock_ip_block(db: Session, *, block_id: int, actor: User, reason: str | None = None) -> IpBlockRead:
    row = db.get(IpBlock, block_id)
    if row is None:
        raise IpBlockError("IP block not found.")
    if not _is_active(row):
        raise IpBlockError("This IP block is no longer active.")
    row.unblocked_at = utc_now()
    row.unblocked_by_user_id = actor.id
    row.unblocked_by_username = actor.username
    row.unblock_reason = (reason or "").strip() or None
    db.commit()
    db.refresh(row)
    return to_read(row)


def list_ip_blocks(
    db: Session,
    *,
    status: str = "active",
    search: str | None = None,
    limit: int = 200,
) -> list[IpBlockRead]:
    now = utc_now()
    query = select(IpBlock)
    if status == "active":
        query = query.where(
            IpBlock.unblocked_at.is_(None),
            or_(IpBlock.expires_at.is_(None), IpBlock.expires_at > now),
        )
    elif status == "expired":
        query = query.where(
            IpBlock.unblocked_at.is_(None),
            IpBlock.expires_at.is_not(None),
            IpBlock.expires_at <= now,
        )
    elif status == "unblocked":
        query = query.where(IpBlock.unblocked_at.is_not(None))
    elif status != "all":
        raise IpBlockError("Invalid IP block status filter.")
    if search:
        needle = search.strip()
        query = query.where(
            or_(
                IpBlock.ip_address.contains(needle),
                IpBlock.reason.contains(needle),
                IpBlock.created_by_username.contains(needle),
            )
        )
    rows = db.scalars(query.order_by(IpBlock.created_at.desc(), IpBlock.id.desc()).limit(limit)).all()
    return [to_read(row, now) for row in rows]


def ip_block_summary(db: Session) -> IpBlockSummary:
    now = utc_now()
    total = int(db.scalar(select(func.count(IpBlock.id))) or 0)
    active_filter = (
        IpBlock.unblocked_at.is_(None),
        or_(IpBlock.expires_at.is_(None), IpBlock.expires_at > now),
    )
    active = int(db.scalar(select(func.count(IpBlock.id)).where(*active_filter)) or 0)
    permanent = int(
        db.scalar(select(func.count(IpBlock.id)).where(*active_filter, IpBlock.expires_at.is_(None))) or 0
    )
    temporary = int(
        db.scalar(select(func.count(IpBlock.id)).where(*active_filter, IpBlock.expires_at.is_not(None))) or 0
    )
    expired = int(
        db.scalar(
            select(func.count(IpBlock.id)).where(
                IpBlock.unblocked_at.is_(None),
                IpBlock.expires_at.is_not(None),
                IpBlock.expires_at <= now,
            )
        )
        or 0
    )
    unblocked = int(db.scalar(select(func.count(IpBlock.id)).where(IpBlock.unblocked_at.is_not(None))) or 0)
    return IpBlockSummary(
        total=total,
        active=active,
        permanent=permanent,
        temporary=temporary,
        expired=expired,
        unblocked=unblocked,
    )
