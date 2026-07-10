from fastapi import APIRouter, Depends

from app.core.dependencies import require_user
from app.modules.accounts.models.user import User

router = APIRouter()


@router.get("/home")
def get_home(_: User = Depends(require_user)) -> dict[str, object]:
    """Return member workspace metadata; user-facing copy is localized in the frontend."""

    return {
        "route": "/home",
        "title": "Royal Blackwater Fleet",
        "focus": "newcomer_onboarding_and_fleet_operations",
        "activity_window": {
            "timezone": "CET",
            "main": "12:00-02:00",
            "port_battles": "18:00-23:00",
        },
        "voice_policy": {
            "competitive": "required",
            "general": "optional_encouraged",
        },
        "modules": [
            {"key": "builds", "status": "available", "access": "member"},
            {"key": "guides", "status": "available", "access": "member"},
            {"key": "forum", "status": "available", "access": "member"},
            {"key": "calendar", "status": "available", "access": "member"},
            {"key": "groups", "status": "available", "access": "member"},
        ],
    }
