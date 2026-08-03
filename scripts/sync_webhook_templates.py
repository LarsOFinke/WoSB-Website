#!/usr/bin/env python3
"""Synchronize copy-ready Discord templates with the runtime defaults."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/src"))

from app.modules.admin.services.webhook_events import DEFAULT_MESSAGES  # noqa: E402


def main() -> None:
    template_dir = ROOT / "docs/integrations/webhook-templates/message-templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    expected = {f"{event_type}.txt" for event_type in DEFAULT_MESSAGES}
    for stale in template_dir.glob("*.txt"):
        if stale.name not in expected:
            stale.unlink()
    for event_type, message in sorted(DEFAULT_MESSAGES.items()):
        (template_dir / f"{event_type}.txt").write_text(
            f"{message.strip()}\n", encoding="utf-8"
        )

    sections = [
        "# Discord webhook message templates",
        "",
        "Generated from the versioned backend defaults. Use the Staff Panel presets for",
        "moderation, operations or public calendar channels and customize only when needed.",
    ]
    for event_type, message in sorted(DEFAULT_MESSAGES.items()):
        sections.extend(
            ("", f"## `{event_type}`", "", "```text", message.strip(), "```")
        )
    (ROOT / "docs/integrations/webhook-templates/all-message-templates.md").write_text(
        "\n".join(sections) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
