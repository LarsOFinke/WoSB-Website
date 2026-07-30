from __future__ import annotations

import json
import re
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any
from urllib.request import Request

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.secret_box import SecretBoxError, webhook_secret_box
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.modules.accounts.models.user import User
from app.modules.admin.services.outbound_webhook_delivery_service.discord import render_message
from app.modules.admin.services.outbound_webhook_delivery_service.transport import WebhookTransport
from app.modules.calendar.models.fleet_event import FleetEvent
from app.modules.calendar.constants import FLEET_EVENT_CATEGORY_VALUES
from app.modules.fleet.services.fleet_service import can_manage_fleet
from app.modules.raid_helper.models.raid_helper import (
    RaidHelperDestination,
    RaidHelperEventLink,
    RaidHelperProfile,
    RaidHelperTemplate,
)
from app.modules.raid_helper.schemas.raid_helper import (
    RaidHelperDispatchSelection,
    RaidHelperEventLinkRead,
    RaidHelperOptionDestination,
    RaidHelperOptionTemplate,
    RaidHelperProfileTestResult,
)
from app.modules.raid_helper.services.errors import RaidHelperError
from app.modules.raid_helper.payload_policy import validate_payload_capability
from app.modules.raid_helper.services.raid_helper_configuration import (
    _validate_base_url,
    create_profile,
    delete_destination,
    delete_profile,
    delete_template,
    list_destinations,
    list_profiles,
    list_templates,
    save_destination,
    save_template,
    update_profile,
)
from app.modules.squads.services.squad_service import can_manage_squad, get_squad_model

def _can_manage_event_scope(db: Session, user: User, squad_id: int | None) -> bool:
    if squad_id is None:
        return can_manage_fleet(db, user)
    squad = get_squad_model(db, squad_id)
    return bool(squad and squad.is_active and can_manage_squad(db, user, squad))


def integration_options(db: Session, user: User, *, category: str, squad_id: int | None) -> list[RaidHelperOptionDestination]:
    category = category.strip().lower()
    if category not in FLEET_EVENT_CATEGORY_VALUES:
        raise RaidHelperError("Invalid event category.")
    if not _can_manage_event_scope(db, user, squad_id):
        raise RaidHelperError("Event management access required.")
    scope_type = "squad" if squad_id is not None else "fleet"
    rows = db.scalars(
        select(RaidHelperDestination)
        .where(
            RaidHelperDestination.is_active.is_(True),
            RaidHelperDestination.scope_type == scope_type,
            RaidHelperDestination.squad_id == squad_id,
        )
        .order_by(RaidHelperDestination.is_default.desc(), RaidHelperDestination.name)
    ).unique().all()
    result: list[RaidHelperOptionDestination] = []
    for row in rows:
        allowed = {item.category for item in row.categories}
        if allowed and category not in allowed:
            continue
        templates: list[RaidHelperOptionTemplate] = []
        for template in row.profile.templates:
            categories = {item.category for item in template.categories}
            if not template.is_active or template.scope_type not in {"both", scope_type} or (categories and category not in categories):
                continue
            templates.append(RaidHelperOptionTemplate(
                id=template.id, name=template.name, profile_id=template.profile_id,
                profile_name=template.profile.name, raid_template_id=template.raid_template_id,
                is_default=template.is_default,
            ))
        if not row.profile.is_active:
            continue
        if templates:
            templates.sort(key=lambda value: (not value.is_default, value.name.lower()))
            result.append(RaidHelperOptionDestination(
                id=row.id, name=row.name, profile_id=row.profile_id, profile_name=row.profile.name,
                scope_type=row.scope_type, squad_id=row.squad_id, is_default=row.is_default,
                default_leader_id=row.profile.default_leader_id,
                templates=templates,
            ))
    return result


def configure_event_links(db: Session, event: FleetEvent, selections: list[RaidHelperDispatchSelection], user: User) -> None:
    options = integration_options(db, user, category=event.category, squad_id=event.squad_id)
    allowed = {
        (destination.id, template.id): destination
        for destination in options
        for template in destination.templates
    }
    requested = {(item.destination_id, item.template_id) for item in selections}
    if not requested.issubset(allowed):
        raise RaidHelperError("One or more Raid-Helper destinations or templates are not valid for this event.")
    existing = {row.destination_id: row for row in db.scalars(select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event.id)).all()}
    requested_destinations = {item.destination_id for item in selections}
    for selection in selections:
        destination = allowed[(selection.destination_id, selection.template_id)]
        if not selection.leader_id and not destination.default_leader_id:
            raise RaidHelperError(
                f'Raid-Helper destination "{destination.name}" requires a leader ID. '
                "Set a profile default or enter one for this appointment."
            )
        row = existing.get(selection.destination_id)
        if row is None:
            db.add(RaidHelperEventLink(
                event_id=event.id,
                destination_id=selection.destination_id,
                template_id=selection.template_id,
                leader_id_override=selection.leader_id,
                status="queued",
                last_operation="create",
            ))
        else:
            row.template_id = selection.template_id
            row.leader_id_override = selection.leader_id
            row.status = "queued"
            row.last_operation = "update" if row.external_event_id else "create"
            row.error_message = None
    for destination_id, row in existing.items():
        if destination_id not in requested_destinations:
            if row.external_event_id:
                row.status = "queued"
                row.last_operation = "delete"
            else:
                db.delete(row)
    db.flush()


def _link_read(row: RaidHelperEventLink) -> RaidHelperEventLinkRead:
    return RaidHelperEventLinkRead(
        id=row.id, destination_id=row.destination_id, destination_name=row.destination.name,
        profile_name=row.destination.profile.name,
        template_id=row.template_id, template_name=row.template.name,
        external_event_id=row.external_event_id, status=row.status, last_operation=row.last_operation,
        error_message=row.error_message, synced_at=row.synced_at,
    )


def serialize_event_links(rows: list[RaidHelperEventLink]) -> list[RaidHelperEventLinkRead]:
    return [_link_read(row) for row in rows]


def event_links(db: Session, event_id: int) -> list[RaidHelperEventLinkRead]:
    rows = db.scalars(select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event_id).order_by(RaidHelperEventLink.id)).unique().all()
    return serialize_event_links(list(rows))


def _normalized_api_key(value: str) -> str:
    """Normalize common copy/paste wrappers without weakening validation."""
    key = value.strip()
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in {"\"", "'"}:
        key = key[1:-1].strip()
    if not key or any(character in key for character in "\r\n"):
        raise RaidHelperError("Stored Raid-Helper API key is empty or malformed.")
    return key


def _normalized_template_id(value: str | None) -> str | None:
    """Return an explicit custom template ID, or None for Raid-Helper's default template.

    Earlier releases prefilled the literal ``Standard`` even though the API's
    templateId field is optional. That made the minimal destination probe pass
    while real calendar delivery could be rejected as an unauthorized template
    request. Treat that legacy application default as no explicit template.
    """
    template_id = (value or "").strip()
    if not template_id or template_id.casefold() == "standard":
        return None
    return template_id


def _auth_headers(profile: RaidHelperProfile) -> dict[str, str]:
    try:
        key = webhook_secret_box.decrypt(profile.api_key_encrypted)
    except SecretBoxError as exc:
        raise RaidHelperError("Stored Raid-Helper API key could not be decrypted.") from exc
    # Raid-Helper's v4 server API expects the API key as the raw value of
    # Authorization. It is not an OAuth bearer token and does not use X-API-Key.
    return {"Authorization": _normalized_api_key(key)}


_RAID_HELPER_TRANSPORT = WebhookTransport(timeout_seconds=10)


def _request(
    profile: RaidHelperProfile,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    base = _validate_base_url(profile.api_base_url)
    headers = {
        **_auth_headers(profile),
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "RoyalBlackwaterFleet-RaidHelper/1.0",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = Request(
        f"{base}{path}",
        data=data,
        headers=headers,
        method=method.upper(),
    )
    status_code, response_text = _RAID_HELPER_TRANSPORT.send(request)
    body: Any
    if not response_text:
        body = None
    else:
        try:
            body = json.loads(response_text)
        except ValueError:
            body = response_text[:1000]
    return status_code, body


def test_profile(db: Session, profile_id: int) -> RaidHelperProfileTestResult | None:
    """Check server read access without claiming event-create authorization."""
    row = db.get(RaidHelperProfile, profile_id)
    if row is None:
        return None
    try:
        status_code, _ = _request(row, "GET", f"/servers/{row.server_id}/events")
    except Exception as exc:
        return RaidHelperProfileTestResult(ok=False, message=f"Connection failed: {type(exc).__name__}")
    ok = 200 <= status_code < 300
    message = (
        "Raid-Helper server read access succeeded. Test the exact channel destination to verify event creation."
        if ok
        else "Raid-Helper rejected the saved profile or server configuration."
    )
    return RaidHelperProfileTestResult(ok=ok, status_code=status_code, message=message)


def test_destination(
    db: Session,
    destination_id: int,
    *,
    template_id: int | None = None,
    use_minimal_payload: bool = False,
) -> RaidHelperProfileTestResult | None:
    from app.modules.raid_helper.services.raid_helper_probe_service import (
        test_destination as run_probe,
    )

    return run_probe(
        db,
        destination_id,
        template_id=template_id,
        use_minimal_payload=use_minimal_payload,
    )


def _event_context(event: FleetEvent, template: RaidHelperTemplate) -> dict[str, Any]:
    start_utc = event.start_at.replace(tzinfo=timezone.utc) if event.start_at.tzinfo is None else event.start_at.astimezone(timezone.utc)
    end_utc = event.end_at.replace(tzinfo=timezone.utc) if event.end_at.tzinfo is None else event.end_at.astimezone(timezone.utc)
    try:
        profile_timezone = ZoneInfo(template.profile.timezone)
    except ZoneInfoNotFoundError as exc:
        raise RaidHelperError("The configured Raid-Helper profile timezone is invalid.") from exc
    start = start_utc.astimezone(profile_timezone)
    end = end_utc.astimezone(profile_timezone)
    duration = max(1, int((end_utc - start_utc).total_seconds() // 60))
    scope_name = event.squad.name if event.squad else "Fleet"
    context: dict[str, Any] = {
        "event": {
            "id": event.id, "title": event.title, "category": event.category,
            "description": event.description or "", "location": event.location or "",
            "start_at": start.isoformat(), "end_at": end.isoformat(),
            "start_at_utc": start_utc.isoformat(), "end_at_utc": end_utc.isoformat(),
            "start_unix": int(start_utc.timestamp()), "end_unix": int(end_utc.timestamp()),
            "date": start.strftime("%d.%m.%Y"), "time": start.strftime("%H:%M"),
            "duration_minutes": duration, "all_day": event.all_day,
            "timezone": template.profile.timezone,
            "timezone_abbreviation": start.tzname() or template.profile.timezone,
            "utc_offset": start.strftime("%z")[:3] + ":" + start.strftime("%z")[3:],
            "start_discord": f"<t:{int(start_utc.timestamp())}:F>",
            "end_discord": f"<t:{int(end_utc.timestamp())}:F>",
            "start_discord_relative": f"<t:{int(start_utc.timestamp())}:R>",
        },
        "scope": {"type": "squad" if event.squad_id else "fleet", "name": scope_name, "squad_id": event.squad_id or ""},
        "raid_helper": {"template_id": _normalized_template_id(template.raid_template_id) or ""},
    }
    context["rendered"] = {
        "title": render_message(template.title_template, context),
        "description": render_message(template.description_template, context),
        "announcement": render_message(template.announcement_template, context),
    }
    return context


_EXACT_TEMPLATE_TOKEN = re.compile(r"^\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}$")


def _context_value(context: dict[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return ""
        current = current[part]
    return "" if current is None else current


def _render_json(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        token = _EXACT_TEMPLATE_TOKEN.fullmatch(value.strip())
        if token:
            # Preserve the actual type of exact placeholders. This keeps numeric
            # fields such as duration as integers while ensuring numeric-looking
            # identifiers (notably templateId) remain strings.
            return _context_value(context, token.group(1))
        return render_message(value, context)
    if isinstance(value, list):
        return [_render_json(item, context) for item in value]
    if isinstance(value, dict):
        return {key: _render_json(item, context) for key, item in value.items() if item is not None}
    return value


def _payload(event: FleetEvent, template: RaidHelperTemplate, leader_id: str) -> dict[str, Any]:
    try:
        validate_payload_capability(
            raid_template_id=template.raid_template_id,
            payload_template_json=template.payload_template_json,
            uses_premium_features=getattr(template, "uses_premium_features", False),
        )
    except ValueError as exc:
        raise RaidHelperError(str(exc)) from exc
    context = _event_context(event, template)
    context["raid_helper"]["leader_id"] = leader_id
    value = json.loads(template.payload_template_json)
    payload = _render_json(value, context)
    if not isinstance(payload, dict):
        raise RaidHelperError("Raid-Helper payload template must render to a JSON object.")
    # templateId is optional. Do not send the legacy application default
    # ``Standard`` or an empty placeholder: Raid-Helper can interpret an explicit
    # template request as a separate authorization decision and return HTTP 401.
    if not _normalized_template_id(template.raid_template_id) or not str(payload.get("templateId", "")).strip():
        payload.pop("templateId", None)
    # Raid-Helper requires leaderId for event creation. Keep this field under
    # application control so every custom payload receives the validated value.
    payload["leaderId"] = leader_id
    return payload


def _effective_leader_id(link: RaidHelperEventLink) -> str:
    leader_id = link.leader_id_override or link.destination.profile.default_leader_id
    if not leader_id:
        raise RaidHelperError(
            "Raid-Helper leader ID is missing. Set a profile default or edit the appointment selection."
        )
    return leader_id


def _external_id(body: Any) -> str | None:
    if isinstance(body, dict):
        for key in ("id", "eventId", "event_id", "messageId", "message_id"):
            if body.get(key) is not None:
                return str(body[key])
        event = body.get("event")
        if isinstance(event, dict):
            return _external_id(event)
    return None


def sync_event(event_id: int, operation: str = "sync") -> None:
    with SessionLocal() as db:
        links = db.scalars(select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event_id)).unique().all()
        for link in links:
            if operation == "cancel":
                link.last_operation = "delete"
                link.status = "queued"
            _sync_link(db, link)



def _response_error_reason(body: Any) -> str | None:
    """Return a bounded, non-structural Raid-Helper error reason for staff UI."""
    if not isinstance(body, dict):
        return None
    for key in ("message", "error", "detail"):
        value = body.get(key)
        if isinstance(value, str):
            reason = " ".join(value.split())
            if reason:
                return reason[:240]
    errors = body.get("errors")
    if isinstance(errors, list):
        reasons = [" ".join(item.split()) for item in errors if isinstance(item, str) and item.strip()]
        if reasons:
            return "; ".join(reasons)[:240]
    return None


def _failed_request_message(status_code: int, body: Any) -> str:
    reason = _response_error_reason(body)
    if status_code == 401:
        base = (
            "Raid-Helper rejected this event payload (HTTP 401). "
            "Test the exact destination with the same application template; an explicit templateId or "
            "permission-dependent advanced option may be unauthorized even when the API key is valid."
        )
    else:
        base = f"Raid-Helper returned HTTP {status_code}."
    return f"{base} {reason}" if reason else base

def _sync_link(db: Session, link: RaidHelperEventLink) -> None:
    link.attempts += 1
    link.last_attempt_at = utc_now()
    try:
        if link.last_operation != "delete" and (
            not link.destination.is_active
            or not link.destination.profile.is_active
            or not link.template.is_active
        ):
            raise RaidHelperError("Raid-Helper profile, destination or template is inactive.")
        if link.last_operation == "delete":
            if not link.external_event_id:
                db.delete(link)
                db.commit()
                return
            status_code, body = _request(link.destination.profile, "DELETE", f"/events/{link.external_event_id}")
        elif link.external_event_id:
            status_code, body = _request(link.destination.profile, "PATCH", f"/events/{link.external_event_id}", _payload(link.event, link.template, _effective_leader_id(link)))
            link.last_operation = "update"
        else:
            path = f"/servers/{link.destination.profile.server_id}/channels/{link.destination.channel_id}/event"
            status_code, body = _request(link.destination.profile, "POST", path, _payload(link.event, link.template, _effective_leader_id(link)))
            link.last_operation = "create"
        link.response_status = status_code
        if 200 <= status_code < 300:
            if link.last_operation == "create":
                external_id = _external_id(body)
                if not external_id:
                    raise RaidHelperError("Raid-Helper response did not include an event ID.")
                link.external_event_id = external_id
            if link.last_operation == "delete":
                db.delete(link)
                db.commit()
                return
            link.status = "delivered"
            link.error_message = None
            link.synced_at = utc_now()
        else:
            link.status = "failed"
            link.error_message = _failed_request_message(status_code, body)
    except Exception as exc:
        link.status = "failed"
        link.error_message = str(exc)[:1000]
    db.commit()


def queue_existing_links_for_update(db: Session, event_id: int) -> None:
    for row in db.scalars(select(RaidHelperEventLink).where(RaidHelperEventLink.event_id == event_id)).all():
        row.status = "queued"
        row.last_operation = "update" if row.external_event_id else "create"
        row.error_message = None
    db.commit()

