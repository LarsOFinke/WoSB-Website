from __future__ import annotations

from datetime import timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.modules.raid_helper.models.raid_helper import (
    RaidHelperDestination,
    RaidHelperTemplate,
)
from app.modules.raid_helper.schemas.raid_helper import RaidHelperProfileTestResult
from app.modules.raid_helper.services.errors import RaidHelperError
from app.modules.raid_helper.services import raid_helper_service


def _destination_test_template(
    destination: RaidHelperDestination,
    template_id: int | None,
) -> RaidHelperTemplate | None:
    active_templates = sorted(
        (template for template in destination.profile.templates if template.is_active),
        key=lambda template: (not template.is_default, template.id),
    )
    if template_id is None:
        return active_templates[0] if active_templates else None
    for template in active_templates:
        if template.id == template_id:
            return template
    raise RaidHelperError(
        "The selected Raid-Helper template is inactive or does not belong to this destination profile."
    )


def _temporary_test_event(
    destination: RaidHelperDestination,
    template: RaidHelperTemplate,
    starts_at,
):
    squad = None
    squad_id = None
    if destination.scope_type == "squad" or template.scope_type == "squad":
        squad_id = destination.squad_id or 1
        squad = SimpleNamespace(
            name=destination.squad.name if destination.squad else "Test squad"
        )
    category = next(
        (row.category for row in template.categories),
        next((row.category for row in destination.categories), "meeting"),
    )
    return SimpleNamespace(
        id=0,
        title="Royal Blackwater Fleet connection test",
        category=category,
        description=(
            "Temporary API verification event. It should be removed automatically."
        ),
        location="Raid-Helper API test",
        start_at=starts_at.astimezone(timezone.utc),
        end_at=(starts_at + timedelta(hours=1)).astimezone(timezone.utc),
        all_day=False,
        squad_id=squad_id,
        squad=squad,
    )


def test_destination(
    db: Session,
    destination_id: int,
    *,
    template_id: int | None = None,
    use_minimal_payload: bool = False,
) -> RaidHelperProfileTestResult | None:
    """Create and immediately delete an event using the calendar payload path."""
    row = db.get(RaidHelperDestination, destination_id)
    if row is None:
        return None
    profile = row.profile
    leader_id = profile.default_leader_id
    if not leader_id:
        return RaidHelperProfileTestResult(
            ok=False,
            message="Configure a default leader ID before testing this destination.",
        )
    try:
        zone = ZoneInfo(profile.timezone)
    except ZoneInfoNotFoundError:
        return RaidHelperProfileTestResult(
            ok=False,
            message="The configured Raid-Helper timezone is invalid.",
        )

    try:
        template = (
            None
            if use_minimal_payload
            else _destination_test_template(row, template_id)
        )
    except RaidHelperError as exc:
        return RaidHelperProfileTestResult(ok=False, message=str(exc))

    starts_at = (
        utc_now().replace(tzinfo=timezone.utc) + timedelta(minutes=15)
    ).astimezone(zone)
    if template is None:
        payload = {
            "leaderId": leader_id,
            "title": "Royal Blackwater Fleet connection test",
            "description": (
                "Temporary API verification event. It should be removed automatically."
            ),
            "date": starts_at.strftime("%d.%m.%Y"),
            "time": starts_at.strftime("%H:%M"),
        }
        template_label = "minimal default payload"
    else:
        try:
            payload = raid_helper_service._payload(
                _temporary_test_event(row, template, starts_at),
                template,
                leader_id,
            )
        except RaidHelperError as exc:
            return RaidHelperProfileTestResult(ok=False, message=str(exc))
        template_label = f'template "{template.name}"'

    path = f"/servers/{profile.server_id}/channels/{row.channel_id}/event"
    try:
        status_code, body = raid_helper_service._request(profile, "POST", path, payload)
    except Exception as exc:
        return RaidHelperProfileTestResult(
            ok=False,
            message=f"Destination test failed: {type(exc).__name__}",
        )

    if not 200 <= status_code < 300:
        message = _probe_failure_message(status_code, body, template, template_label)
        return RaidHelperProfileTestResult(
            ok=False,
            status_code=status_code,
            message=message,
        )

    external_id = raid_helper_service._external_id(body)
    if not external_id:
        return RaidHelperProfileTestResult(
            ok=False,
            status_code=status_code,
            message=(
                "The temporary event was created, but Raid-Helper returned no "
                "event ID for cleanup."
            ),
        )

    try:
        delete_status, delete_body = raid_helper_service._request(
            profile,
            "DELETE",
            f"/events/{external_id}",
        )
    except Exception as exc:
        return RaidHelperProfileTestResult(
            ok=False,
            status_code=status_code,
            message=(
                "The temporary event was created, but automatic cleanup failed: "
                f"{type(exc).__name__}."
            ),
        )
    if not 200 <= delete_status < 300:
        return RaidHelperProfileTestResult(
            ok=False,
            status_code=delete_status,
            message=(
                "The temporary event was created, but Raid-Helper could not delete "
                f"it automatically. {raid_helper_service._failed_request_message(delete_status, delete_body)}"
            ),
        )
    return RaidHelperProfileTestResult(
        ok=True,
        status_code=status_code,
        message=(
            "Raid-Helper event creation and cleanup succeeded for "
            f"{template_label}."
        ),
    )


def _probe_failure_message(
    status_code: int,
    body,
    template: RaidHelperTemplate | None,
    template_label: str,
) -> str:
    if status_code != 401:
        return raid_helper_service._failed_request_message(status_code, body)
    if template is None:
        return (
            "Raid-Helper rejected event creation for this destination (HTTP 401). "
            "Re-enter the exact API key used by a working create-event request and "
            "verify the server/channel IDs."
        )
    explicit_template_id = raid_helper_service._normalized_template_id(template.raid_template_id)
    if explicit_template_id:
        return (
            f"Raid-Helper rejected {template_label} (HTTP 401). The destination and "
            "API key may be valid, but templateId "
            f'"{explicit_template_id}" is not authorized for this server. Leave the '
            "template ID blank to use the server default, or verify custom-template "
            "access."
        )
    return (
        f"Raid-Helper rejected {template_label} (HTTP 401). Review premium or "
        "permission-dependent advanced kwargs in the payload template."
    )
