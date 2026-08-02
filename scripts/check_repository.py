#!/usr/bin/env python3
"""Fast repository invariants used locally and in CI."""

from __future__ import annotations

import argparse
import ast
from configparser import ConfigParser
import json
import re
import runpy
import subprocess
import sys
from pathlib import Path

# Repository validation must not create bytecode in the tree it validates.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/src"))

parser = argparse.ArgumentParser(description="Validate repository invariants.")
parser.add_argument(
    "--strict-tree",
    action="store_true",
    help="reject tracked generated/runtime artifacts in Git, or every such artifact in exported source trees",
)
ARGS = parser.parse_args()

VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
SCAN_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".venv-build",
    ".vite",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "release",
}

STRICT_FORBIDDEN_DIRS = {
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".venv-build",
    ".vite",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "release",
}
STRICT_FORBIDDEN_SUFFIXES = {
    ".AppImage",
    ".agekey",
    ".db",
    ".deb",
    ".dll",
    ".dylib",
    ".exe",
    ".jks",
    ".key",
    ".keystore",
    ".msi",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".rpm",
    ".sha256",
    ".so",
    ".sqlite",
    ".sqlite3",
    ".tar",
    ".tgz",
    ".zip",
}
STRICT_FORBIDDEN_NAME_SUFFIXES = (".tar.gz",)


def fail(message: str) -> None:
    raise SystemExit(f"[repository-check] {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def git_tracked_files() -> set[Path] | None:
    """Return tracked paths in a Git checkout, or None for exported source trees."""
    try:
        top_level = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        if Path(top_level.stdout.strip()).resolve() != ROOT.resolve():
            return None
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return {
        Path(value.decode("utf-8", errors="surrogateescape"))
        for value in result.stdout.split(b"\0")
        if value
    }


STRICT_TRACKED_FILES = git_tracked_files() if ARGS.strict_tree else None


def strict_relative_in_scope(relative: Path) -> bool:
    return STRICT_TRACKED_FILES is None or relative in STRICT_TRACKED_FILES


pyproject = (ROOT / "backend/pyproject.toml").read_text(encoding="utf-8")
application_config_path = ROOT / "backend/config/application.cfg"
application_config = ConfigParser(interpolation=None)
loaded_application_config = application_config.read(
    application_config_path, encoding="utf-8"
)
require(
    loaded_application_config == [str(application_config_path)],
    "could not read backend/config/application.cfg",
)
require(application_config.has_section("app"), "application.cfg is missing [app]")
package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
require(re.fullmatch(r"\d+\.\d+\.\d+", VERSION) is not None, "VERSION is not semantic")
require(
    re.search(rf'^version = "{re.escape(VERSION)}"$', pyproject, re.MULTILINE)
    is not None,
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
    "AGENTS.md",
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
    "docs/QUALITY_STANDARDS.md",
    "docs/QUALITY_AUDIT_2026-08.md",
    "docs/CONTAINER_SECURITY.md",
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
    "scripts/clean_repository.sh",
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
require(
    not any(config_dir.glob("*.toml")),
    "legacy TOML configuration remains in backend/config",
)
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
    for forbidden in sorted(STRICT_FORBIDDEN_DIRS):
        if STRICT_TRACKED_FILES is None:
            found = [path for path in ROOT.rglob(forbidden) if ".git" not in path.parts]
            display = found[0] if found else forbidden
        else:
            found = [
                relative
                for relative in STRICT_TRACKED_FILES
                if forbidden in relative.parts
            ]
            display = found[0] if found else forbidden
        require(not found, f"generated directory in release tree: {display}")

    generated_locale_prefix = Path("frontend/src/locales/generated")
    if STRICT_TRACKED_FILES is None:
        generated_locales_found = (ROOT / generated_locale_prefix).exists()
    else:
        generated_locales_found = any(
            relative == generated_locale_prefix
            or generated_locale_prefix in relative.parents
            for relative in STRICT_TRACKED_FILES
        )
    require(
        not generated_locales_found,
        "generated locale modules must be rebuilt by npm scripts, not shipped as source",
    )

    if STRICT_TRACKED_FILES is None:
        egg_info = [
            path for path in ROOT.rglob("*.egg-info") if ".git" not in path.parts
        ]
    else:
        egg_info = [
            relative
            for relative in STRICT_TRACKED_FILES
            if any(part.endswith(".egg-info") for part in relative.parts)
        ]
    require(
        not egg_info,
        f"package metadata in release tree: {egg_info[0] if egg_info else '.egg-info'}",
    )

for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in SCAN_EXCLUDED_DIRS for part in path.parts):
        continue
    relative = path.relative_to(ROOT)
    if ARGS.strict_tree and strict_relative_in_scope(relative):
        require(
            path.suffix not in STRICT_FORBIDDEN_SUFFIXES
            and not path.name.endswith(STRICT_FORBIDDEN_NAME_SUFFIXES),
            f"generated, packaged or sensitive file in release tree: {relative}",
        )
        require(
            not (path.name.startswith(".env") and not path.name.endswith(".example")),
            f"runtime environment in release tree: {relative}",
        )
        require(
            path.name != "first-run-credentials.txt",
            f"generated credentials in release tree: {relative}",
        )
        require(
            not path.name.endswith(".egg-info"),
            f"package metadata in release tree: {relative}",
        )
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
require(
    migration_files[0].name == "0001_baseline.py",
    "baseline migration filename must be 0001_baseline.py",
)
previous_revision: str | None = None
seen_revisions: set[str] = set()
for index, migration_file in enumerate(migration_files):
    migration_text = migration_file.read_text(encoding="utf-8")
    revision_match = re.search(
        r"^revision: str = [\"']([^\"']+)[\"']$", migration_text, re.MULTILINE
    )
    require(
        revision_match is not None, f"migration has no revision: {migration_file.name}"
    )
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
            re.search(r"^down_revision: .* = None$", migration_text, re.MULTILINE)
            is not None,
            "baseline migration must not depend on historical revisions",
        )
    else:
        down_match = re.search(
            r"^down_revision: .* = [\"']([^\"']+)[\"']$", migration_text, re.MULTILINE
        )
        require(
            down_match is not None,
            f"migration has no single down revision: {migration_file.name}",
        )
        require(
            down_match.group(1) == previous_revision,
            f"migration chain is not linear at {migration_file.name}",
        )
    previous_revision = revision

# Builds persist only user-authored inputs and normalized references. Derived
# statistics must always be calculated from the current ship/effect catalog.
from app.modules.registry import register_all_models  # noqa: E402
from app.modules.builds.models.build import Build  # noqa: E402
from app.modules.builds.models.build_slot import BuildSlot  # noqa: E402

register_all_models()
expected_build_columns = {
    "id",
    "build_name",
    "build_type",
    "ship_id",
    "owner_id",
    "is_official_template",
    "research_upgrade_feature_id",
    "mortar_modification_installed",
    "sailors",
    "soldiers",
    "musketeers",
    "mercenaries",
    "details",
    "created_at",
    "updated_at",
}
expected_build_slot_columns = {
    "id",
    "build_id",
    "slot_type",
    "slot_index",
    "option_id",
    "quantity",
    "created_at",
    "updated_at",
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
    "ship_stats",
    "effective_stats",
    "base_stats",
    "stat_rows",
    "item_effects",
    "calculated_stats",
    "result_snapshot",
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
        if path.suffix not in {
            ".py",
            ".js",
            ".mjs",
            ".vue",
            ".sh",
            ".yml",
            ".yaml",
            ".conf",
            ".md",
            ".txt",
        }:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        for token in legacy_discord_tokens:
            require(
                token not in source,
                f"retired Discord integration token {token!r} in {path.relative_to(ROOT)}",
            )

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
require(
    "broadcast_enabled" in webhook_model_source,
    "webhook model is missing broadcast targets",
)
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
    "event",
    "occurred_at",
    "destination",
    "actor",
    "resource",
    "scope",
    "data",
    "source",
    "id",
}
for event_type, template_path in template_files.items():
    template_text = template_path.read_text(encoding="utf-8").strip()
    require(template_text, f"empty webhook template: {event_type}")
    require(
        default_messages[event_type] == template_text,
        f"backend autofill/default template differs from repository template: {event_type}",
    )
    require(
        len(template_text) <= 1800,
        f"webhook template too long for Discord: {event_type}",
    )
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
    require(
        path.stat().st_size <= 250_000,
        f"JavaScript module exceeds 250 KB: {path.relative_to(ROOT)}",
    )
    require(
        ";base64," not in path.read_text(encoding="utf-8", errors="ignore"),
        f"embedded base64 payload in {path.relative_to(ROOT)}",
    )

# Keep executable responsibilities bounded. Large declarative catalogs may span
# more lines, but a single Python class/function or Vue script controller may not.
python_responsibility_roots = (
    ROOT / "backend/src",
    ROOT / "infrastructure/scripts/backup",
    ROOT / "tools/recovery-tool/src",
)
for responsibility_root in python_responsibility_roots:
    for path in responsibility_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                span = (node.end_lineno or node.lineno) - node.lineno + 1
                require(
                    span <= 420,
                    f"Python responsibility exceeds 420 lines: {path.relative_to(ROOT)}::{node.name} ({span})",
                )
for path in (ROOT / "frontend/src").rglob("*.vue"):
    source = path.read_text(encoding="utf-8")
    script_match = re.search(
        r"<script(?:\s+setup)?[^>]*>(.*?)</script>", source, re.DOTALL
    )
    if script_match:
        script_lines = len(script_match.group(1).splitlines())
        require(
            script_lines <= 420,
            f"Vue script responsibility exceeds 420 lines: {path.relative_to(ROOT)} ({script_lines})",
        )

# Keep the global cascade deterministic without returning to the historical
# 11k-line stylesheet. JavaScript imports preserve order without the production
# extraction differences previously caused by nested CSS @imports.
styles_root = ROOT / "frontend/src/styles"
global_styles_root = styles_root / "global"
global_styles_manifest = global_styles_root / "index.js"
require(
    not (styles_root / "main.css").exists(),
    "monolithic frontend/src/styles/main.css must not return",
)
require(global_styles_manifest.is_file(), "global CSS cascade manifest is missing")
manifest_source = global_styles_manifest.read_text(encoding="utf-8")
manifest_styles = re.findall(r"import './(\d{2}-[^']+\.css)'", manifest_source)
require(
    manifest_styles and manifest_styles[0] == "00-tokens.css",
    "global CSS must start with tokens",
)
require(
    len(manifest_styles) == len(set(manifest_styles)),
    "global CSS manifest contains duplicates",
)
require(
    [int(filename[:2]) for filename in manifest_styles]
    == sorted(int(filename[:2]) for filename in manifest_styles),
    "global CSS numeric cascade order changed",
)
global_style_sources = []
for filename in manifest_styles:
    path = global_styles_root / filename
    require(path.is_file(), f"global CSS layer is missing: {filename}")
    source = path.read_text(encoding="utf-8")
    require("@import" not in source, f"CSS @import is forbidden in {filename}")
    require(
        path.stat().st_size <= 75_000, f"global CSS layer exceeds 75 KB: {filename}"
    )
    require(
        len(source.splitlines()) <= 420,
        f"global CSS responsibility exceeds 420 lines: {filename}",
    )
    global_style_sources.append(source)
main_styles = "\n".join(global_style_sources)
require(
    main_styles.lstrip().startswith(":root"),
    "global CSS must start with the token layer",
)
require(
    len(re.findall(r"(?m)^:root\s*\{", main_styles)) == 1,
    "global CSS must expose exactly one :root block",
)
require(
    "--font-display:" in global_style_sources[0], "display font token must be defined"
)
require(
    main_styles.count("!important") <= 28, "global CSS exceeds the !important budget"
)
all_css = list((ROOT / "frontend/src").rglob("*.css"))
for path in all_css:
    require(
        len(path.read_text(encoding="utf-8").splitlines()) <= 420,
        f"CSS responsibility exceeds 420 lines: {path.relative_to(ROOT)}",
    )
require(
    sum(path.stat().st_size for path in all_css) <= 400_000,
    "frontend CSS exceeds the 400 KB source budget",
)
require(
    (ROOT / "docs/CSS_ARCHITECTURE.md").is_file(),
    "CSS architecture documentation is missing",
)
require((ROOT / "scripts/audit_css.py").is_file(), "CSS audit script is missing")
require(
    (ROOT / "frontend/scripts/check-responsive-css.mjs").is_file(),
    "responsive CSS quality gate is missing",
)
require(
    (ROOT / "docs/DATA_RETENTION.md").is_file(),
    "data-retention documentation is missing",
)
webhook_event_facade = ROOT / "backend/src/app/modules/admin/services/webhook_events.py"
require(webhook_event_facade.is_file(), "webhook event compatibility facade is missing")
require(
    (
        ROOT / "backend/src/app/modules/admin/services/webhook_event_catalog.py"
    ).is_file(),
    "webhook event catalog module is missing",
)
require(
    (
        ROOT / "backend/src/app/modules/admin/services/webhook_event_samples.py"
    ).is_file(),
    "webhook event sample module is missing",
)
require(
    line_count(webhook_event_facade) <= 60,
    "webhook event facade must remain a thin compatibility layer",
)
require(
    (ROOT / "docs/SECURITY_PRIVACY_AUDIT.md").is_file(),
    "security/privacy audit is missing",
)
workflow_sources = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
)
for supported_action in (
    "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38",
    "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f",
    "aquasecurity/trivy-action@a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8",
    "google/osv-scanner-action/.github/workflows/osv-scanner-reusable",
    "@3adb4b14a2b0623876d18d863a498b785fb3752d",
):
    require(
        supported_action in workflow_sources,
        f"approved GitHub Action missing: {supported_action}",
    )
require(
    "pull_request_target:" not in workflow_sources,
    "pull_request_target workflows are forbidden",
)

# API responses embed the smallest useful identity instead of full user profiles.
for schema_path in (
    ROOT / "backend/src/app/modules/groups/schemas/group_read.py",
    ROOT / "backend/src/app/modules/guides/schemas/guide_summary.py",
    ROOT / "backend/src/app/modules/forum/schemas/forum_thread_summary.py",
    ROOT / "backend/src/app/modules/forum/schemas/forum_post_read.py",
    ROOT / "backend/src/app/modules/calendar/schemas/fleet_event_read.py",
):
    schema_source = schema_path.read_text(encoding="utf-8")
    require(
        "UserReferenceRead" in schema_source,
        f"nested full user profile returned by {schema_path.relative_to(ROOT)}",
    )
    require(
        "UserRead" not in schema_source.replace("UserReferenceRead", ""),
        f"nested UserRead returned by {schema_path.relative_to(ROOT)}",
    )

maintenance_config = (ROOT / "backend/config/uploads.cfg").read_text(encoding="utf-8")
for retention_key in (
    "webhook_delivery_retention_days",
    "cookie_consent_retention_days",
    "resolved_privacy_request_retention_days",
    "pending_registration_retention_days",
    "reviewed_registration_retention_days",
):
    require(
        retention_key in maintenance_config,
        f"maintenance retention key is missing: {retention_key}",
    )

# Route pages are composition-only: network and lifecycle workflows belong in
# page-model composables, where they can be tested independently.
route_pages = sorted((ROOT / "frontend/src/modules").glob("*/pages/*Page.vue"))
require(
    len(route_pages) == 37,
    "route page inventory changed; update the architecture budget",
)
for page_path in route_pages:
    page_source = page_path.read_text(encoding="utf-8")
    script_match = re.search(r"<script setup>([\s\S]*?)</script>", page_source)
    script_source = script_match.group(1) if script_match else ""
    require(
        "/api/" not in script_source,
        f"route page imports API transport directly: {page_path.relative_to(ROOT)}",
    )
    require(
        re.search(r"\basync\s+(?:function|\()", script_source) is None,
        f"route page owns an async workflow: {page_path.relative_to(ROOT)}",
    )
    require(
        "onMounted(" not in script_source,
        f"route page owns lifecycle loading: {page_path.relative_to(ROOT)}",
    )
    require(
        re.search(
            r"\buse(?:[A-Z][A-Za-z0-9]+Page|AdminWorkspace|MasterDataWorkspace|BuildDesigner|FleetManagePage|NewcomerGuidePage)\s*\(",
            script_source,
        )
        is not None,
        f"route page has no dedicated page model: {page_path.relative_to(ROOT)}",
    )

# Production containers use explicit runtime versions. Local application image
# names remain configurable through Compose, but third-party bases may not float.
backend_dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
frontend_dockerfile = (ROOT / "infrastructure/docker/frontend.Dockerfile").read_text(
    encoding="utf-8"
)
compose_source = (ROOT / "infrastructure/compose.yml").read_text(encoding="utf-8")
require(
    "FROM python:3.12.13-slim-bookworm AS runtime" in backend_dockerfile,
    "backend Python image is not pinned",
)
require(
    "pip install --upgrade pip" not in backend_dockerfile,
    "backend image performs an unpinned pip upgrade",
)
require(
    "FROM node:22.23.1-alpine3.24 AS build" in frontend_dockerfile,
    "frontend Node image is not pinned",
)
require(
    "FROM nginx:1.27.5-alpine3.21 AS runtime" in frontend_dockerfile,
    "gateway NGINX image is not pinned",
)
require(
    "image: postgres:16.14-alpine3.24" in compose_source,
    "PostgreSQL image is not pinned",
)
require(
    "image: louislam/uptime-kuma:1.23.16" in compose_source,
    "Uptime Kuma image is not pinned",
)

# The shared stylesheet must not regain the retired staff dashboard. The active
# implementation is isolated in the named modules/admin/styles/staff*.css files.
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
require(
    not legacy_seed_dir.exists(), "legacy Python seed package remains in backend/src"
)
seed_dir = ROOT / "backend/seeds"
manifest_path = seed_dir / "manifest.json"
require(manifest_path.is_file(), "master-data manifest is missing")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
require(manifest.get("schema_version") == 1, "unsupported master-data manifest version")
document_paths = [str(row.get("path", "")) for row in manifest.get("documents", [])]
require(
    len(document_paths) == len(set(document_paths)),
    "duplicate master-data manifest path",
)
declared_json = {(seed_dir / path).resolve() for path in document_paths}
actual_json = {
    path.resolve()
    for path in seed_dir.rglob("*.json")
    if path.resolve() != manifest_path.resolve()
}
require(
    declared_json == actual_json,
    "master-data manifest does not cover the complete JSON tree",
)
require(
    not any(seed_dir.rglob("*.py")),
    "executable Python must not be stored with JSON master data",
)
seed_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore") for path in actual_json
)
for marker in (
    "Starter Template:",
    "Evening PvE Farming Run",
    "Practice feedback: line turns",
    "seed_starter_content",
):
    require(
        marker not in seed_text,
        f"user-facing example content remains in production seeds: {marker}",
    )

# Growth budgets are deliberately generous for the v1 baseline but prevent
# coordinator pages and services from silently becoming unbounded monoliths.
for path in (ROOT / "backend/src/app/modules").rglob("*.py"):
    if "services" in path.parts:
        require(
            line_count(path) <= 525,
            f"service exceeds 525-line budget: {path.relative_to(ROOT)}",
        )
for path in (ROOT / "backend/src/app/modules").rglob("*.py"):
    if "routes" in path.parts:
        require(
            line_count(path) <= 300,
            f"route module exceeds 300-line budget: {path.relative_to(ROOT)}",
        )
for path in (ROOT / "frontend/src/modules").rglob("*.vue"):
    if "pages" in path.parts:
        require(
            line_count(path) <= 1050,
            f"page exceeds 1050-line budget: {path.relative_to(ROOT)}",
        )

require(not any((ROOT / "docs").glob("RELEASE_0_*")), "legacy release documents remain")
require(
    not any((ROOT / "docs").glob("UI_UX_RELEASE_*")),
    "legacy UI release documents remain",
)

backup_required_files = {
    "backend/src/app/modules/admin/routes/backups.py",
    "backend/src/app/modules/admin/schemas/backup_control.py",
    "backend/src/app/modules/admin/services/backup_control_service.py",
    "backend/src/app/modules/admin/services/backup_control_repository.py",
    "frontend/src/modules/admin/pages/DatabaseBackupsPage.vue",
    "frontend/src/modules/admin/composables/useDatabaseBackupsPage.js",
    "frontend/src/modules/admin/composables/useBackupEnrollment.js",
    "infrastructure/scripts/backup/backup-admin-runner.py",
    "infrastructure/scripts/backup/backup_runner_core.py",
    "infrastructure/scripts/backup/backup_runner_enrollment.py",
    "infrastructure/scripts/backup/backup_runner_transfer.py",
    "infrastructure/scripts/backup/backup_runner_restore.py",
    "infrastructure/scripts/backup/local_backup_catalog.py",
    "infrastructure/scripts/backup/arm-admin-restore.sh",
    "infrastructure/scripts/services/backup-from-admin.sh",
    "tools/recovery-tool/rbf-recovery-tool.spec",
    "tools/recovery-tool/src/rbf_recovery_tool/app.py",
    "tools/recovery-tool/src/rbf_recovery_tool/platform_support.py",
    "tools/recovery-tool/src/rbf_recovery_tool/verification.py",
    "tools/recovery-tool/src/rbf_recovery_tool/docker_lab.py",
    "tools/recovery-tool/src/rbf_recovery_tool/automation.py",
    "tools/recovery-tool/src/rbf_recovery_tool/cli.py",
    "tools/recovery-tool/src/rbf_recovery_tool/linux_setup.py",
    "tools/windows/recovery-tool/Build-RbfRecoveryTool.ps1",
    "tools/linux/recovery-tool/Build-RbfRecoveryTool.sh",
    "tools/linux/recovery-tool/Install-RbfRecoveryTool.sh",
    "tools/linux/recovery-tool/Provision-RbfRecoveryLab.sh",
    "tools/linux/recovery-tool/Setup-RbfRecoveryLab.sh",
    "tools/linux/recovery-tool/Build-RbfRecoveryInstaller.sh",
    "tools/linux/recovery-tool/Build-RbfRecoveryDeb.sh",
    "infrastructure/systemd/rbf-hub-backup-admin.path",
    "infrastructure/systemd/rbf-hub-backup-admin.service",
}
for relative_path in backup_required_files:
    require(
        (ROOT / relative_path).is_file(),
        f"missing backup control file: {relative_path}",
    )

backup_route = (ROOT / "backend/src/app/modules/admin/routes/backups.py").read_text(
    encoding="utf-8"
)
require(
    "Depends(require_admin)" in backup_route, "backup routes must remain admin-only"
)
require(
    "Depends(require_bootstrap_admin)" in backup_route,
    "database restores must require the bootstrap administrator",
)
require(
    '"/local/restore"' in backup_route and '"restore_postgresql"' in backup_route,
    "protected local database restore route is missing",
)
require(
    "approval_token_sha256" in backup_route and '"approval_token":' not in backup_route,
    "plaintext restore approval tokens must never be queued",
)
backup_runner_modules = (
    "backup-admin-runner.py",
    "backup_runner_core.py",
    "backup_runner_enrollment.py",
    "backup_runner_transfer.py",
    "backup_runner_restore.py",
)
backup_runner = "\n".join(
    (ROOT / "infrastructure/scripts/backup" / name).read_text(encoding="utf-8")
    for name in backup_runner_modules
)
require(
    "StrictHostKeyChecking=yes" in backup_runner,
    "remote backups must verify SSH host keys",
)
require(
    "sftp-roundtrip" in backup_runner,
    "remote backups must record SFTP round-trip verification",
)
require(
    "get {source.name}" in backup_runner,
    "remote backups must re-download uploaded artifacts for verification",
)
require(
    "sha256sum -c" not in backup_runner,
    "SFTP-only backup accounts must not require a remote shell",
)
restore_runner_block = (
    ROOT / "infrastructure/scripts/backup/backup_runner_restore.py"
).read_text(encoding="utf-8")
require(
    restore_runner_block.index("consume_database_restore_approval")
    < restore_runner_block.index("resolve_local_postgres_backup"),
    "database restore approval must be consumed before catalog or compression work",
)
backup_schema = (
    ROOT / "backend/src/app/modules/admin/schemas/backup_control.py"
).read_text(encoding="utf-8")
backup_summary_block = backup_schema.split("class BackupConnectionSummary", 1)[1].split(
    "class BackupControlStatus", 1
)[0]
require(
    "private_key:" not in backup_summary_block,
    "backup status schema must not expose private-key material",
)
require(
    "SecretStr" in backup_schema,
    "database restore approval tokens must use secret schema fields",
)
require(
    "log_tail" not in backup_schema,
    "host backup logs must not be exposed through the website",
)
local_catalog = (
    ROOT / "infrastructure/scripts/backup/local_backup_catalog.py"
).read_text(encoding="utf-8")
for marker in ("O_NOFOLLOW", "compare_digest", "token_sha256", "backup_id"):
    require(
        marker in local_catalog, f"local backup catalog hardening is missing: {marker}"
    )
recovery_backup_script = (
    ROOT / "infrastructure/scripts/backup/backup-recovery.sh"
).read_text(encoding="utf-8")
require(
    "! -name 'database-restore-approval.json'" in recovery_backup_script,
    "ephemeral database-restore approvals must never enter recovery bundles",
)
recovery_gui = (
    ROOT / "tools/recovery-tool/src/rbf_recovery_tool/sftp_client.py"
).read_text(encoding="utf-8")
require(
    "PinnedFingerprintPolicy" in recovery_gui, "recovery tool must pin SSH host keys"
)
require(
    "AutoAddPolicy" not in recovery_gui,
    "recovery tool must not auto-trust SSH host keys",
)
recovery_verification = (
    ROOT / "tools/recovery-tool/src/rbf_recovery_tool/verification.py"
).read_text(encoding="utf-8")
recovery_spec = (ROOT / "tools/recovery-tool/rbf-recovery-tool.spec").read_text(
    encoding="utf-8"
)
for marker in (
    "age.exe",
    '"age"',
    "age-keygen.exe",
    '"age-keygen"',
    "verify_sidecar",
    "_validated_members",
):
    require(
        marker in recovery_verification or marker in recovery_spec,
        f"cross-platform recovery tool frozen verification is missing: {marker}",
    )
linux_build = (ROOT / "tools/linux/recovery-tool/Build-RbfRecoveryTool.sh").read_text(
    encoding="utf-8"
)
windows_build = (
    ROOT / "tools/windows/recovery-tool/Build-RbfRecoveryTool.ps1"
).read_text(encoding="utf-8")
require(
    "../../recovery-tool" in linux_build, "Linux recovery build must use shared source"
)
require(
    "recovery-tool" in windows_build, "Windows recovery build must use shared source"
)
require(
    "--noconfirm" in linux_build,
    "Linux recovery build must be reproducible and non-interactive",
)
require(
    'rm -rf -- "$BUILD_DIR" "$DIST_DIR"' in linux_build
    and linux_build.index('rm -rf -- "$BUILD_DIR" "$DIST_DIR"')
    < linux_build.index("age wurde nicht gefunden"),
    "Linux recovery build must clear stale output before prerequisite validation",
)
require(
    "Remove-Item -LiteralPath $Dist -Recurse -Force" in windows_build
    and windows_build.index("Remove-Item -LiteralPath $Dist -Recurse -Force")
    < windows_build.index("age.exe wurde nicht gefunden"),
    "Windows recovery build must clear stale output before prerequisite validation",
)
linux_install = (
    ROOT / "tools/linux/recovery-tool/Install-RbfRecoveryTool.sh"
).read_text(encoding="utf-8")
require(
    ".local/bin" in linux_install and "rbf-recovery-tool" in linux_install,
    "Linux recovery installer must remain user-local",
)
require("sudo" not in linux_install, "Linux recovery installer must not require root")
recovery_lab = (
    ROOT / "tools/recovery-tool/src/rbf_recovery_tool/docker_lab.py"
).read_text(encoding="utf-8")
for marker in (
    "127.0.0.1",
    "no-new-privileges:true",
    "read_only: true",
    "postgres:16.14-alpine3.24",
):
    require(
        marker in recovery_lab,
        f"local recovery database lab hardening is missing: {marker}",
    )
require(
    "127.0.0.1:${{POSTGRES_LOCAL_PORT}}:5432" in recovery_lab,
    "local recovery database lab must remain loopback-only",
)
preflight_override = recovery_lab.split("def _application_preflight_override", 1)[
    1
].split("def verify_recovery", 1)[0]
require(
    "networks: [rbf_recovery_backend]" in preflight_override,
    "recovery application preflight must use the internal lab network",
)
require(
    "ports:" not in preflight_override,
    "recovery application preflight must not publish host ports",
)
rootless_setup = (ROOT / "tools/linux/recovery-tool/Setup-RbfRecoveryLab.sh").read_text(
    encoding="utf-8"
)
require(
    "rootless" in rootless_setup and "docker group" not in rootless_setup,
    "Linux DB lab must use rootless Docker",
)
provisioner = (
    ROOT / "tools/linux/recovery-tool/Provision-RbfRecoveryLab.sh"
).read_text(encoding="utf-8")
require(
    "download.docker.com/linux/ubuntu" in provisioner,
    "Docker provisioning must use the official Ubuntu repository",
)
require(
    "usermod -aG docker" not in provisioner,
    "Recovery lab must not grant docker-group root privileges",
)
deb_builder = (ROOT / "tools/linux/recovery-tool/Build-RbfRecoveryDeb.sh").read_text(
    encoding="utf-8"
)
require(
    "dpkg-deb" in deb_builder and "/usr/lib/rbf-recovery-tool" in deb_builder,
    "Linux recovery tool must produce an installable Debian package with root-owned helpers",
)
require("pkexec" in deb_builder, "Linux recovery Debian package must depend on pkexec")
require(
    re.search(r"^Depends:.*\bpolicykit-1\b", deb_builder, re.MULTILINE) is None,
    "obsolete policykit-1 package dependency must not return",
)
require(
    'cd "$DIST_DIR"' in deb_builder and 'sha256sum "$OUTPUT_NAME"' in deb_builder,
    "Debian package checksum must contain a portable basename",
)
require(
    'find "$DIST_DIR" -maxdepth 1 -type f' in deb_builder
    and deb_builder.index('find "$DIST_DIR" -maxdepth 1 -type f')
    < deb_builder.index("Binary fehlt oder ist nicht ausführbar"),
    "standalone Debian packaging must remove stale packages before input validation",
)
installer_builder = (
    ROOT / "tools/linux/recovery-tool/Build-RbfRecoveryInstaller.sh"
).read_text(encoding="utf-8")
require(
    'cd "$DIST_DIR"' in installer_builder
    and 'sha256sum "$ARCHIVE_NAME"' in installer_builder,
    "portable installer checksum must contain a portable basename",
)
require(
    'rm -f -- "$ARCHIVE" "$ARCHIVE.sha256"' in installer_builder
    and installer_builder.index('rm -f -- "$ARCHIVE" "$ARCHIVE.sha256"')
    < installer_builder.index("Binary fehlt oder ist nicht ausführbar"),
    "standalone installer packaging must remove stale archives before input validation",
)
linux_setup = (
    ROOT / "tools/recovery-tool/src/rbf_recovery_tool/linux_setup.py"
).read_text(encoding="utf-8")
require(
    "require_root_owned=True" in linux_setup and "pkexec" in linux_setup,
    "privileged Linux recovery setup must execute only a root-owned helper through PolicyKit",
)

print(f"Repository invariants OK (v{VERSION}).")
