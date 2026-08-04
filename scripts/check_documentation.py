#!/usr/bin/env python3
"""Validate stable local references in tracked Markdown documentation."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"!?\[[^]]*]\(([^)]+)\)")
FORBIDDEN_COMMANDS = {
    "python scripts/": "use python3 for repository scripts",
    "scripts/run_browser_smoke.py": "use frontend npm run test:browser",
}


def tracked_markdown_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", "*.md"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / value for value in result.stdout.split("\0") if value]


def local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target.split("#", 1)[0])
    if not target or target.startswith(("http://", "https://", "mailto:", "/")):
        return None
    return target


def main() -> None:
    failures: list[str] = []
    markdown_files = tracked_markdown_files()
    for path in markdown_files:
        content = path.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(content):
            target = local_link_target(raw_target)
            if target and not (path.parent / target).resolve().exists():
                failures.append(f"{path.relative_to(ROOT)}: missing local link {target}")
        for token, guidance in FORBIDDEN_COMMANDS.items():
            if token in content:
                failures.append(f"{path.relative_to(ROOT)}: {token!r} is stale; {guidance}")
    if failures:
        raise SystemExit("[documentation] " + "\n[documentation] ".join(failures))
    print(f"[documentation] OK: {len(markdown_files)} tracked Markdown files")


if __name__ == "__main__":
    main()
