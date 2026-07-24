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
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    ".github/workflows/deploy.yml",
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
    if not path.is_file() or ".git" in path.parts:
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
        if not path.is_file() or any(part in {"node_modules", "__pycache__"} for part in path.parts):
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
print(f"Repository invariants OK (v{VERSION}).")
