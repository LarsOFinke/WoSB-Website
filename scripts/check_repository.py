#!/usr/bin/env python3
"""Fast repository invariants used locally and in CI."""
from __future__ import annotations

import argparse
from configparser import ConfigParser
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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


# The historical migration chain is intentionally squashed into one immutable baseline.
migration_files = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
require(len(migration_files) == 1, "database schema must have exactly one baseline migration")
baseline_text = migration_files[0].read_text(encoding="utf-8")
require("revision: str = '0001_baseline'" in baseline_text, "unexpected baseline revision")
require(
    "down_revision: Union[str, Sequence[str], None] = None" in baseline_text,
    "baseline migration must not depend on historical revisions",
)

# Prevent generated or embedded payloads from turning source modules into binary containers.
for path in (ROOT / "frontend/src").rglob("*.js"):
    require(path.stat().st_size <= 250_000, f"JavaScript module exceeds 250 KB: {path.relative_to(ROOT)}")
    require(";base64," not in path.read_text(encoding="utf-8", errors="ignore"), f"embedded base64 payload in {path.relative_to(ROOT)}")

# Production seed sources must contain only operational and master data.
seed_dir = ROOT / "backend/src/app/seeds"
for forbidden_name in ("starter_content.py", "newcomer_guide.py", "legacy_demo_cleanup.py"):
    require(not (seed_dir / forbidden_name).exists(), f"production mock seed remains: {forbidden_name}")
seed_text = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in seed_dir.glob("*.py")
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
