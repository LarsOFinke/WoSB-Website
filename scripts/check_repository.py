#!/usr/bin/env python3
"""Fast repository invariants used locally and in CI."""
from __future__ import annotations

import argparse
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
app_config = (ROOT / "backend/config/app.toml").read_text(encoding="utf-8")
package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
require(re.fullmatch(r"\d+\.\d+\.\d+", VERSION) is not None, "VERSION is not semantic")
require(
    re.search(rf'^version = "{re.escape(VERSION)}"$', pyproject, re.MULTILINE) is not None,
    "backend version mismatch",
)
require(
    re.search(rf'^version = "{re.escape(VERSION)}"$', app_config, re.MULTILINE) is not None,
    "app version mismatch",
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

if ARGS.strict_tree:
    for forbidden in ("node_modules", "dist", ".pytest_cache", ".ruff_cache", "__pycache__"):
        found = [path for path in ROOT.rglob(forbidden) if ".git" not in path.parts]
        require(not found, f"generated directory in release tree: {found[0] if found else forbidden}")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    relative = path.relative_to(ROOT)
    if ARGS.strict_tree:
        require(path.suffix not in {".pyc", ".pyo"}, f"compiled Python file in release tree: {relative}")
        require(path.name != ".env", f"runtime environment in release tree: {relative}")
    if (
        path.suffix in {".json", ".js", ".mjs", ".md", ".toml", ".yml", ".yaml", ".txt"}
        or path.name == "Dockerfile"
    ):
        text = path.read_text(encoding="utf-8", errors="ignore")
        require(
            "packages.applied-caas-gateway" not in text,
            f"internal package registry in {relative}",
        )

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
        require(line_count(path) <= 550, f"service exceeds 550-line budget: {path.relative_to(ROOT)}")
for path in (ROOT / "frontend/src/modules").rglob("*.vue"):
    if "pages" in path.parts:
        require(line_count(path) <= 1000, f"page exceeds 1000-line budget: {path.relative_to(ROOT)}")

require(not any((ROOT / "docs").glob("RELEASE_0_*")), "legacy release documents remain")
require(not any((ROOT / "docs").glob("UI_UX_RELEASE_*")), "legacy UI release documents remain")
print(f"Repository invariants OK (v{VERSION}).")
