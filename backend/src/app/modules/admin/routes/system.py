from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.discord_bot import (
    DiscordBotConfigurationUpdate,
    DiscordBotRequest,
    DiscordBotRequestResult,
    DiscordBotStatus,
)
from app.modules.admin.schemas.system_update import (
    SystemUpdateRequest,
    SystemUpdateRequestResult,
    SystemUpdateStatus,
)
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.discord_bot_manager_service import (
    DiscordBotManagerError,
    get_discord_bot_status,
    request_discord_bot_configuration,
    request_discord_bot_operation,
)
from app.modules.admin.services.system_update_service import (
    SystemUpdateError,
    get_system_update_status,
    request_system_update,
)

router = APIRouter(prefix="/system", tags=["admin-system"])


@router.get("/update", response_model=SystemUpdateStatus)
def admin_system_update_status(_: User = Depends(require_admin)) -> SystemUpdateStatus:
    return get_system_update_status()


@router.post(
    "/update",
    response_model=SystemUpdateRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_request_system_update(
    current_user: User = Depends(require_admin),
    payload: SystemUpdateRequest | None = None,
) -> SystemUpdateRequestResult:
    operation = payload.operation if payload is not None else "update"
    try:
        update_status = request_system_update(current_user, operation)
    except SystemUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return SystemUpdateRequestResult(accepted=True, status=update_status)


@router.get("/discord-bot", response_model=DiscordBotStatus)
def admin_discord_bot_status(_: User = Depends(require_admin)) -> DiscordBotStatus:
    return get_discord_bot_status()


@router.post(
    "/discord-bot",
    response_model=DiscordBotRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_request_discord_bot_operation(
    payload: DiscordBotRequest,
    current_user: User = Depends(require_admin),
) -> DiscordBotRequestResult:
    try:
        bot_status = request_discord_bot_operation(current_user, payload.operation)
    except DiscordBotManagerError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return DiscordBotRequestResult(accepted=True, status=bot_status)


@router.put(
    "/discord-bot/configuration",
    response_model=DiscordBotRequestResult,
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_configure_discord_bot(
    payload: DiscordBotConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DiscordBotRequestResult:
    try:
        bot_status = request_discord_bot_configuration(current_user, payload)
    except DiscordBotManagerError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="discord_bot_configuration",
        entity_id="runtime",
        action="update",
        summary="Discord bot runtime configuration queued for host application.",
        changed_fields=(
            ["website_base_url", "channels", "suppress_notifications"]
            + (["discord_bot_token"] if payload.discord_bot_token else [])
            + (["webhook_secret"] if payload.webhook_secret else [])
        ),
    )
    return DiscordBotRequestResult(accepted=True, status=bot_status)
