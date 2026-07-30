"""Domain model registry for SQLAlchemy metadata registration."""

from importlib import import_module

_MODEL_MODULES = (
    "app.modules.accounts.models.auth_session",
    "app.modules.accounts.models.registration_request",
    "app.modules.accounts.models.user",
    "app.modules.accounts.models.user_profile",
    "app.modules.permissions.models.role",
    "app.modules.privacy.models.cookie_consent",
    "app.modules.legal.models.legal_notice",
    "app.modules.admin.models.security_event",
    "app.modules.admin.models.audit_log",
    "app.modules.admin.models.ip_block",
    "app.modules.admin.models.outbound_webhook",
    "app.modules.builds.models.build",
    "app.modules.builds.models.build_feature",
    "app.modules.builds.models.build_role",
    "app.modules.builds.models.build_vote",
    "app.modules.builds.models.build_classification",
    "app.modules.builds.models.build_item_category",
    "app.modules.builds.models.build_item_effect",
    "app.modules.builds.models.build_item_option",
    "app.modules.builds.models.build_item_option_slot",
    "app.modules.builds.models.weapon_performance",
    "app.modules.builds.models.build_option",
    "app.modules.builds.models.build_slot",
    "app.modules.squads.models.squad",
    "app.modules.squads.models.squad_member",
    "app.modules.calendar.models.fleet_event",
    "app.modules.files.models.file_asset",
    "app.modules.fleet.models.fleet",
    "app.modules.fleet.models.fleet_membership",
    "app.modules.forum.models.forum",
    "app.modules.forum.models.forum_post",
    "app.modules.forum.models.forum_post_attachment",
    "app.modules.groups.models.group",
    "app.modules.groups.models.group_member",
    "app.modules.guides.models.guide",
    "app.modules.guides.models.guide_attachment",
    "app.modules.guides.models.guide_build_reference",
    "app.modules.onboarding.models.newcomer_guide",
    "app.modules.ships.models.ship",
    "app.modules.ships.models.mortar_modification",
    "app.modules.ships.models.rate_weapon_class",
    "app.modules.ships.models.ship_upgrade_effect",
    "app.modules.ships.models.weapon_mount",
)


def register_all_models() -> None:
    """Import all ORM model modules so SQLAlchemy metadata is complete."""
    for module_name in _MODEL_MODULES:
        import_module(module_name)
