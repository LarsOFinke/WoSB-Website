#!/usr/bin/env python3
"""Fast repository invariants used locally and in CI."""
from __future__ import annotations

import argparse
import ast
from configparser import ConfigParser
import json
import re
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/src"))

parser = argparse.ArgumentParser(description="Validate repository invariants.")
parser.add_argument(
    "--strict-tree",
    action="store_true",
    help="also reject local/generated/runtime artifacts; use for clean checkouts and release archives",
)
ARGS = parser.parse_args()

VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
SCAN_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
}


def fail(message: str) -> None:
    raise SystemExit(f"[repository-check] {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


pyproject = (ROOT / "backend/pyproject.toml").read_text(encoding="utf-8")
application_config_path = ROOT / "backend/config/application.cfg"
application_config = ConfigParser(interpolation=None)
loaded_application_config = application_config.read(application_config_path, encoding="utf-8")
require(
    loaded_application_config == [str(application_config_path)],
    "could not read backend/config/application.cfg",
)
require(application_config.has_section("app"), "application.cfg is missing [app]")
package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
require(re.fullmatch(r"\d+\.\d+\.\d+", VERSION) is not None, "VERSION is not semantic")
require(
    re.search(rf'^version = "{re.escape(VERSION)}"$', pyproject, re.MULTILINE) is not None,
    "backend version mismatch",
)
require(
    application_config.get("app", "version", fallback="").strip() == VERSION,
    "application.cfg version mismatch",
)
require(package.get("version") == VERSION, "frontend version mismatch")
require(
    lock.get("version") == VERSION
    and lock.get("packages", {}).get("", {}).get("version") == VERSION,
    "frontend lockfile version mismatch",
)

required_files = {
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "backend/requirements.lock",
    "backend/requirements-dev.lock",
    "docs/GO_LIVE.md",
    "docs/INSTALLATION.md",
    "docs/ARCHITECTURE.md",
    "docs/DEVELOPMENT.md",
    "docs/OPERATIONS.md",
    "docs/DATABASE.md",
    "docs/TESTING.md",
    "docs/DEPLOYMENT.md",
    "docs/UPTIME_KUMA_2_MIGRATION.md",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/security.yml",
    "scripts/security_audit.py",
}
for relative in required_files:
    require((ROOT / relative).is_file(), f"missing {relative}")

required_backend_config = {
    "application.cfg",
    "logging.cfg",
    "session.cfg",
    "uploads.cfg",
    "container.env",
}
config_dir = ROOT / "backend/config"
require(config_dir.is_dir(), "missing backend/config")
for name in required_backend_config:
    require((config_dir / name).is_file(), f"missing backend/config/{name}")
require(not any(config_dir.glob("*.toml")), "legacy TOML configuration remains in backend/config")
container_env_lines = [
    line.strip()
    for line in (config_dir / "container.env").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]
require(
    not container_env_lines,
    "backend/config/container.env must remain assignment-free; Compose injects runtime values",
)

if ARGS.strict_tree:
    for forbidden in (
        "node_modules",
        "dist",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
    ):
        found = [path for path in ROOT.rglob(forbidden) if ".git" not in path.parts]
        require(not found, f"generated directory in release tree: {found[0] if found else forbidden}")
    egg_info = [path for path in ROOT.rglob("*.egg-info") if ".git" not in path.parts]
    require(not egg_info, f"package metadata in release tree: {egg_info[0] if egg_info else '.egg-info'}")

for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in SCAN_EXCLUDED_DIRS for part in path.parts):
        continue
    relative = path.relative_to(ROOT)
    if ARGS.strict_tree:
        require(path.suffix not in {".pyc", ".pyo"}, f"compiled Python file in release tree: {relative}")
        require(path.name != ".env", f"runtime environment in release tree: {relative}")
        require(not path.name.endswith(".egg-info"), f"package metadata in release tree: {relative}")
    if (
        path.suffix in {".json", ".js", ".mjs", ".md", ".toml", ".yml", ".yaml", ".txt"}
        or path.name == "Dockerfile"
    ):
        text = path.read_text(encoding="utf-8", errors="ignore")
        require(
            "packages.applied-caas-gateway" not in text,
            f"internal package registry in {relative}",
        )


# Clean installations start at the production baseline and advance through one
# explicit, linear migration chain.
migration_files = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
require(migration_files, "repository must ship a production baseline migration")
require(migration_files[0].name == "0001_baseline.py", "baseline migration filename must be 0001_baseline.py")
previous_revision: str | None = None
seen_revisions: set[str] = set()
for index, migration_file in enumerate(migration_files):
    migration_text = migration_file.read_text(encoding="utf-8")
    revision_match = re.search(r"^revision: str = [\"']([^\"']+)[\"']$", migration_text, re.MULTILINE)
    require(revision_match is not None, f"migration has no revision: {migration_file.name}")
    revision = revision_match.group(1)
    require(revision not in seen_revisions, f"duplicate migration revision: {revision}")
    require(
        len(revision) <= 32,
        f"migration revision exceeds Alembic version column limit (32): {revision}",
    )
    seen_revisions.add(revision)

    if index == 0:
        require(revision == "0001_baseline", "unexpected baseline revision")
        require(
            re.search(r"^down_revision: .* = None$", migration_text, re.MULTILINE) is not None,
            "baseline migration must not depend on historical revisions",
        )
    else:
        down_match = re.search(r"^down_revision: .* = [\"']([^\"']+)[\"']$", migration_text, re.MULTILINE)
        require(down_match is not None, f"migration has no single down revision: {migration_file.name}")
        require(
            down_match.group(1) == previous_revision,
            f"migration chain is not linear at {migration_file.name}",
        )
    previous_revision = revision

# Builds persist only user-authored inputs and normalized references. Derived
# statistics must always be calculated from the current ship/effect catalog.
from app.modules.registry import register_all_models
from app.modules.builds.models.build import Build
from app.modules.builds.models.build_slot import BuildSlot

register_all_models()
expected_build_columns = {
    "id", "build_name", "build_type", "ship_id", "owner_id",
    "is_official_template", "research_upgrade_feature_id",
    "mortar_modification_installed", "sailors", "soldiers",
    "musketeers", "mercenaries", "details", "created_at", "updated_at",
}
expected_build_slot_columns = {
    "id", "build_id", "slot_type", "slot_index", "option_id", "quantity",
    "created_at", "updated_at",
}
require(
    set(Build.__table__.columns.keys()) == expected_build_columns,
    "builds must contain only authored inputs and foreign-key references; derived result columns are forbidden",
)
require(
    set(BuildSlot.__table__.columns.keys()) == expected_build_slot_columns,
    "build_slots must contain only normalized option references and quantities",
)
for forbidden_result_name in (
    "ship_stats", "effective_stats", "base_stats", "stat_rows",
    "item_effects", "calculated_stats", "result_snapshot",
):
    require(
        forbidden_result_name not in Build.__table__.columns,
        f"derived build result must not be persisted: {forbidden_result_name}",
    )

# Discord integration is intentionally limited to native channel webhooks.
legacy_discord_tokens = (
    "discord_bot",
    "discord-bot",
    "BotSetup",
    "signed_json",
    "signing_secret",
    "delivery_mode",
    "channel_key",
)
for source_root in (ROOT / "backend", ROOT / "frontend", ROOT / "infrastructure"):
    for path in source_root.rglob("*"):
        if not path.is_file() or any(part in SCAN_EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix not in {".py", ".js", ".mjs", ".vue", ".sh", ".yml", ".yaml", ".conf", ".md", ".txt"}:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        for token in legacy_discord_tokens:
            require(token not in source, f"retired Discord integration token {token!r} in {path.relative_to(ROOT)}")

# Discord channel webhooks support independent multi-channel subscriptions and manual broadcasts.
webhook_model_source = (
    ROOT / "backend/src/app/modules/admin/models/outbound_webhook.py"
).read_text(encoding="utf-8")
webhook_route_source = (
    ROOT / "backend/src/app/modules/admin/routes/outbound_webhooks.py"
).read_text(encoding="utf-8")
webhook_schema_source = (
    ROOT / "backend/src/app/modules/admin/schemas/outbound_webhook.py"
).read_text(encoding="utf-8")
broadcast_panel_source = (
    ROOT / "frontend/src/modules/admin/components/DiscordBroadcastPanel.vue"
).read_text(encoding="utf-8")
require("broadcast_enabled" in webhook_model_source, "webhook model is missing broadcast targets")
require(
    '@router.post("/broadcast/send"' in webhook_route_source,
    "manual Discord broadcast route is missing",
)
require(
    "OutboundWebhookBroadcastRequest" in webhook_schema_source,
    "manual Discord broadcast request contract is missing",
)
require(
    "sendDiscordBroadcast" in broadcast_panel_source
    and "form.webhook_ids" in broadcast_panel_source,
    "Discord broadcast panel is missing multi-target delivery",
)
require(
    "UniqueConstraint" not in webhook_model_source,
    "Discord webhook subscriptions must not be unique per event or scope",
)
require(
    "discord_avatar_url" not in webhook_model_source
    and "discord_avatar_url" not in webhook_schema_source,
    "obsolete Discord avatar override remains in the runtime contract",
)
webhook_service_source = (
    ROOT / "backend/src/app/modules/admin/services/outbound_webhook_service.py"
).read_text(encoding="utf-8")
require(
    "webhook_secret_box.encrypt" in webhook_service_source,
    "Discord webhook credentials must be encrypted before persistence",
)

# Every published webhook event must ship with a copy-ready text template.
webhook_event_path = ROOT / "backend/src/app/modules/admin/services/webhook_events.py"
webhook_event_source = webhook_event_path.read_text(encoding="utf-8")
webhook_namespace = runpy.run_path(str(webhook_event_path))
event_catalog = webhook_namespace.get("EVENT_CATALOG")
event_test_samples = webhook_namespace.get("EVENT_TEST_SAMPLES")
default_messages = webhook_namespace.get("DEFAULT_MESSAGES")
require(isinstance(event_catalog, tuple), "webhook EVENT_CATALOG is missing")
require(isinstance(event_test_samples, dict), "webhook EVENT_TEST_SAMPLES is missing")
require(isinstance(default_messages, dict), "webhook DEFAULT_MESSAGES is missing")
webhook_event_types = {row[0] for row in event_catalog}
require(
    set(event_test_samples) == webhook_event_types,
    "webhook test samples must match EVENT_CATALOG exactly",
)
require(
    set(default_messages) == webhook_event_types,
    "webhook DEFAULT_MESSAGES must match EVENT_CATALOG exactly",
)
template_dir = ROOT / "docs/webhook-templates/message-templates"
require(template_dir.is_dir(), "missing copy-ready webhook template directory")
template_files = {path.stem: path for path in template_dir.glob("*.txt")}
require(
    set(template_files) == webhook_event_types,
    "webhook template files must match EVENT_CATALOG exactly",
)
valid_template_roots = {
    "event", "occurred_at", "destination", "actor", "resource", "scope", "data", "source", "id"
}
for event_type, template_path in template_files.items():
    template_text = template_path.read_text(encoding="utf-8").strip()
    require(template_text, f"empty webhook template: {event_type}")
    require(
        default_messages[event_type] == template_text,
        f"backend autofill/default template differs from repository template: {event_type}",
    )
    require(len(template_text) <= 1800, f"webhook template too long for Discord: {event_type}")
    sample = event_test_samples[event_type]
    sample_envelope = {
        "id": "test-delivery",
        "event": event_type,
        "occurred_at": "2026-01-01T00:00:00+00:00",
        "source": "royal-blackwater-fleet",
        "destination": {"name": "Test destination"},
        "actor": {
            "id": 42,
            "username": "test-captain",
            "display_name": "Test Captain",
            "role": "user",
        },
        "scope": {
            "type": sample.get("scope_type", "global"),
            "id": sample.get("scope_id"),
            "fleet_id": sample.get("fleet_id"),
            "squad_id": sample.get("squad_id"),
        },
        "resource": {
            "type": sample["resource_type"],
            "id": str(sample["resource_id"]),
            "url": sample.get("resource_url"),
        },
        "data": sample["data"],
    }
    for token in re.findall(r"\{\{?\s*([a-zA-Z0-9_.-]+)\s*\}?\}", template_text):
        require(
            token.split(".", 1)[0] in valid_template_roots,
            f"unsupported webhook template token in {event_type}: {token}",
        )
        current = sample_envelope
        for part in token.split("."):
            require(
                isinstance(current, dict) and part in current,
                f"webhook template token has no test payload value in {event_type}: {token}",
            )
            current = current[part]
    if event_type != "integration.test":
        require(
            "{resource.url}" in template_text,
            f"linkable webhook template is missing resource URL: {event_type}",
        )
require(
    (ROOT / "docs/webhook-templates/README.md").is_file(),
    "missing webhook template usage guide",
)

# Every domain event must have exactly one production publisher in a route module.
publisher_counts = {event_type: 0 for event_type in webhook_event_types}
for route_path in (ROOT / "backend/src/app/modules").rglob("routes/*.py"):
    route_tree = ast.parse(route_path.read_text(encoding="utf-8"))
    for node in ast.walk(route_tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in publisher_counts:
                publisher_counts[node.value] += 1
for event_type, count in publisher_counts.items():
    if event_type == "integration.test":
        continue
    require(
        count == 1,
        f"webhook event must have exactly one route publisher ({count} found): {event_type}",
    )


# Prevent generated or embedded payloads from turning source modules into binary containers.
for path in (ROOT / "frontend/src").rglob("*.js"):
    require(path.stat().st_size <= 250_000, f"JavaScript module exceeds 250 KB: {path.relative_to(ROOT)}")
    require(";base64," not in path.read_text(encoding="utf-8", errors="ignore"), f"embedded base64 payload in {path.relative_to(ROOT)}")

# Keep the global cascade deterministic without returning to the historical
# 11k-line stylesheet. JavaScript imports preserve order without the production
# extraction differences previously caused by nested CSS @imports.
styles_root = ROOT / "frontend/src/styles"
global_styles_root = styles_root / "global"
global_styles_manifest = global_styles_root / "index.js"
expected_global_styles = [
    "00-tokens.css",
    "10-foundation.css",
    "20-layout.css",
    "30-shell.css",
    "40-navigation-and-portal.css",
    "50-domain-workspaces.css",
    "60-operations.css",
    "70-integrations.css",
]
require(not (styles_root / "main.css").exists(), "monolithic frontend/src/styles/main.css must not return")
require(global_styles_manifest.is_file(), "global CSS cascade manifest is missing")
manifest_source = global_styles_manifest.read_text(encoding="utf-8")
manifest_styles = re.findall(r"import './(\d{2}-[^']+\.css)'", manifest_source)
require(manifest_styles == expected_global_styles, "global CSS cascade order changed")
global_style_sources = []
for filename in expected_global_styles:
    path = global_styles_root / filename
    require(path.is_file(), f"global CSS layer is missing: {filename}")
    source = path.read_text(encoding="utf-8")
    require("@import" not in source, f"CSS @import is forbidden in {filename}")
    require(path.stat().st_size <= 75_000, f"global CSS layer exceeds 75 KB: {filename}")
    require(len(source.splitlines()) <= 3_500, f"global CSS layer exceeds 3,500 lines: {filename}")
    global_style_sources.append(source)
main_styles = "\n".join(global_style_sources)
require(main_styles.lstrip().startswith(":root"), "global CSS must start with the token layer")
require(len(re.findall(r"(?m)^:root\s*\{", main_styles)) == 1, "global CSS must expose exactly one :root block")
require("--font-display:" in global_style_sources[0], "display font token must be defined")
require(main_styles.count("!important") <= 28, "global CSS exceeds the !important budget")
all_css = list((ROOT / "frontend/src").rglob("*.css"))
require(
    sum(path.stat().st_size for path in all_css) <= 400_000,
    "frontend CSS exceeds the 400 KB source budget",
)
require((ROOT / "docs/CSS_ARCHITECTURE.md").is_file(), "CSS architecture documentation is missing")
require((ROOT / "scripts/audit_css.py").is_file(), "CSS audit script is missing")
require((ROOT / "docs/DATA_RETENTION.md").is_file(), "data-retention documentation is missing")
webhook_event_facade = ROOT / "backend/src/app/modules/admin/services/webhook_events.py"
require(webhook_event_facade.is_file(), "webhook event compatibility facade is missing")
require(
    (ROOT / "backend/src/app/modules/admin/services/webhook_event_catalog.py").is_file(),
    "webhook event catalog module is missing",
)
require(
    (ROOT / "backend/src/app/modules/admin/services/webhook_event_samples.py").is_file(),
    "webhook event sample module is missing",
)
require(
    line_count(webhook_event_facade) <= 60,
    "webhook event facade must remain a thin compatibility layer",
)
require((ROOT / "docs/SECURITY_PRIVACY_AUDIT.md").is_file(), "security/privacy audit is missing")
workflow_sources = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
)
for supported_action in (
    "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38",
    "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f",
    "google/osv-scanner-action/.github/workflows/osv-scanner-reusable",
    "@3adb4b14a2b0623876d18d863a498b785fb3752d",
):
    require(supported_action in workflow_sources, f"approved GitHub Action missing: {supported_action}")
require("pull_request_target:" not in workflow_sources, "pull_request_target workflows are forbidden")

# API responses embed the smallest useful identity instead of full user profiles.
for schema_path in (
    ROOT / "backend/src/app/modules/groups/schemas/group_read.py",
    ROOT / "backend/src/app/modules/guides/schemas/guide_summary.py",
    ROOT / "backend/src/app/modules/forum/schemas/forum_thread_summary.py",
    ROOT / "backend/src/app/modules/forum/schemas/forum_post_read.py",
    ROOT / "backend/src/app/modules/calendar/schemas/fleet_event_read.py",
):
    schema_source = schema_path.read_text(encoding="utf-8")
    require("UserReferenceRead" in schema_source, f"nested full user profile returned by {schema_path.relative_to(ROOT)}")
    require("UserRead" not in schema_source.replace("UserReferenceRead", ""), f"nested UserRead returned by {schema_path.relative_to(ROOT)}")

maintenance_config = (ROOT / "backend/config/uploads.cfg").read_text(encoding="utf-8")
for retention_key in (
    "webhook_delivery_retention_days",
    "cookie_consent_retention_days",
    "pending_registration_retention_days",
    "reviewed_registration_retention_days",
):
    require(retention_key in maintenance_config, f"maintenance retention key is missing: {retention_key}")

# Route pages are composition-only: network and lifecycle workflows belong in
# page-model composables, where they can be tested independently.
route_pages = sorted((ROOT / "frontend/src/modules").glob("*/pages/*Page.vue"))
require(len(route_pages) == 33, "route page inventory changed; update the architecture budget")
for page_path in route_pages:
    page_source = page_path.read_text(encoding="utf-8")
    script_match = re.search(r"<script setup>([\s\S]*?)</script>", page_source)
    script_source = script_match.group(1) if script_match else ""
    require("/api/" not in script_source, f"route page imports API transport directly: {page_path.relative_to(ROOT)}")
    require(
        re.search(r"\basync\s+(?:function|\()", script_source) is None,
        f"route page owns an async workflow: {page_path.relative_to(ROOT)}",
    )
    require("onMounted(" not in script_source, f"route page owns lifecycle loading: {page_path.relative_to(ROOT)}")
    require(
        re.search(
            r"\buse(?:[A-Z][A-Za-z0-9]+Page|AdminWorkspace|MasterDataWorkspace|BuildDesigner|FleetManagePage|NewcomerGuidePage)\s*\(",
            script_source,
        ) is not None,
        f"route page has no dedicated page model: {page_path.relative_to(ROOT)}",
    )

# Production containers use explicit runtime versions. Local application image
# names remain configurable through Compose, but third-party bases may not float.
backend_dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
frontend_dockerfile = (ROOT / "infrastructure/docker/frontend.Dockerfile").read_text(encoding="utf-8")
compose_source = (ROOT / "infrastructure/compose.yml").read_text(encoding="utf-8")
require("FROM python:3.12.13-slim-bookworm AS runtime" in backend_dockerfile, "backend Python image is not pinned")
require("pip install --upgrade pip" not in backend_dockerfile, "backend image performs an unpinned pip upgrade")
require("FROM node:22.23.1-alpine3.24 AS build" in frontend_dockerfile, "frontend Node image is not pinned")
require("FROM nginx:1.27.5-alpine3.21 AS runtime" in frontend_dockerfile, "gateway NGINX image is not pinned")
require("image: postgres:16.14-alpine3.24" in compose_source, "PostgreSQL image is not pinned")
require("image: louislam/uptime-kuma:1.23.16" in compose_source, "Uptime Kuma image is not pinned")

# The shared stylesheet must not regain the retired staff dashboard. The active
# implementation is isolated in modules/admin/styles/staffWorkspace.css.
for retired_selector in (
    ".staff-command-card",
    ".staff-command-center",
    ".staff-mobile-tab-picker",
    ".staff-mobile-tab-sheet",
    ".staff-overview-card-grid",
    ".staff-overview-queue-grid",
    ".staff-workspace-frame",
):
    require(
        retired_selector not in main_styles,
        f"retired staff dashboard selector remains in shared CSS: {retired_selector}",
    )

# Production master data must be isolated from application source and every
# JSON document must be declared by the root manifest.
legacy_seed_dir = ROOT / "backend/src/app/seeds"
require(not legacy_seed_dir.exists(), "legacy Python seed package remains in backend/src")
seed_dir = ROOT / "backend/seeds"
manifest_path = seed_dir / "manifest.json"
require(manifest_path.is_file(), "master-data manifest is missing")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
require(manifest.get("schema_version") == 1, "unsupported master-data manifest version")
document_paths = [str(row.get("path", "")) for row in manifest.get("documents", [])]
require(len(document_paths) == len(set(document_paths)), "duplicate master-data manifest path")
declared_json = {(seed_dir / path).resolve() for path in document_paths}
actual_json = {
    path.resolve()
    for path in seed_dir.rglob("*.json")
    if path.resolve() != manifest_path.resolve()
}
require(declared_json == actual_json, "master-data manifest does not cover the complete JSON tree")
require(
    not any(seed_dir.rglob("*.py")),
    "executable Python must not be stored with JSON master data",
)
seed_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in actual_json
)
for marker in (
    "Starter Template:",
    "Evening PvE Farming Run",
    "Practice feedback: line turns",
    "seed_starter_content",
):
    require(marker not in seed_text, f"user-facing example content remains in production seeds: {marker}")

# Growth budgets are deliberately generous for the v1 baseline but prevent
# coordinator pages and services from silently becoming unbounded monoliths.
for path in (ROOT / "backend/src/app/modules").rglob("*.py"):
    if "services" in path.parts:
        require(line_count(path) <= 525, f"service exceeds 525-line budget: {path.relative_to(ROOT)}")
for path in (ROOT / "backend/src/app/modules").rglob("*.py"):
    if "routes" in path.parts:
        require(line_count(path) <= 300, f"route module exceeds 300-line budget: {path.relative_to(ROOT)}")
for path in (ROOT / "frontend/src/modules").rglob("*.vue"):
    if "pages" in path.parts:
        require(line_count(path) <= 1050, f"page exceeds 1050-line budget: {path.relative_to(ROOT)}")

require(not any((ROOT / "docs").glob("RELEASE_0_*")), "legacy release documents remain")
require(not any((ROOT / "docs").glob("UI_UX_RELEASE_*")), "legacy UI release documents remain")

backup_required_files = {
    "backend/src/app/modules/admin/routes/backups.py",
    "backend/src/app/modules/admin/schemas/backup_control.py",
    "backend/src/app/modules/admin/services/backup_control_service.py",
    "frontend/src/modules/admin/pages/DatabaseBackupsPage.vue",
    "frontend/src/modules/admin/composables/useDatabaseBackupsPage.js",
    "infrastructure/scripts/backup/backup-admin-runner.py",
    "infrastructure/scripts/services/backup-from-admin.sh",
    "infrastructure/systemd/rbf-hub-backup-admin.path",
    "infrastructure/systemd/rbf-hub-backup-admin.service",
}
for relative_path in backup_required_files:
    require((ROOT / relative_path).is_file(), f"missing backup control file: {relative_path}")

backup_route = (ROOT / "backend/src/app/modules/admin/routes/backups.py").read_text(encoding="utf-8")
require("Depends(require_admin)" in backup_route, "backup routes must remain admin-only")
backup_runner = (ROOT / "infrastructure/scripts/backup/backup-admin-runner.py").read_text(encoding="utf-8")
require("StrictHostKeyChecking=yes" in backup_runner, "remote backups must verify SSH host keys")
require("sha256sum -c" in backup_runner, "remote backups must verify the uploaded checksum")
backup_schema = (ROOT / "backend/src/app/modules/admin/schemas/backup_control.py").read_text(encoding="utf-8")
backup_summary_block = backup_schema.split("class BackupConnectionSummary", 1)[1].split(
    "class BackupControlStatus", 1
)[0]
require(
    "private_key:" not in backup_summary_block,
    "backup status schema must not expose private-key material",
)

print(f"Repository invariants OK (v{VERSION}).")
