#!/usr/bin/env python3
"""Synchronize the grouped webhook-template reference from the event catalog."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'spring-api/src/main/reference/webhook-events.json'
DOCS = ROOT / 'docs/integrations/webhook-templates'
TARGET = DOCS / 'all-message-templates.md'
LEGACY_DIRECTORY = DOCS / 'message-templates'
JAVA_TARGET = ROOT / 'spring-api/src/main/java/eu/royalblackwater/api/webhooks/service/WebhookEventCatalog.java'
PLACEHOLDER = re.compile(r'\{([a-z][a-z0-9_.]*)}')
SUPPORTED_PLACEHOLDERS = {
    'actor.display_name', 'actor.username', 'data.summary', 'event',
    'occurred_at', 'resource.id', 'resource.type',
}


def title(value: str) -> str:
    return value.replace('_', ' ').replace('-', ' ').title()


def java_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def java_catalog(events: list[dict[str, object]]) -> str:
    rows = ',\n'.join(
        '            new WebhookEventDefinition(%s, %s, %s, %s)' % (
            java_string(row['default_message']), java_string(row.get('description') or ''),
            java_string(row['category']), java_string(row['key']))
        for row in events
    )
    return f'''// Generated from spring-api/src/main/reference/webhook-events.json; do not edit manually.
package eu.royalblackwater.api.webhooks.service;

import eu.royalblackwater.api.webhooks.dto.WebhookEventDefinition;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

public final class WebhookEventCatalog {{
    public static final List<WebhookEventDefinition> ALL = List.of(
{rows}
    );
    public static final Set<String> TYPES = ALL.stream().map(WebhookEventDefinition::key)
            .collect(Collectors.toUnmodifiableSet());

    public static WebhookEventDefinition required(String key) {{
        return ALL.stream().filter(event -> event.key().equals(key)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown webhook event: " + key));
    }}

    private WebhookEventCatalog() {{ }}
}}
'''


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding='utf-8'))
    events = payload.get('events')
    if payload.get('schema_version') != 1 or not isinstance(events, list):
        raise SystemExit('Invalid webhook event catalog')

    keys = [row.get('key') for row in events]
    if any(not key for key in keys) or len(keys) != len(set(keys)):
        raise SystemExit('Webhook keys must be unique')
    messages = [str(row.get('default_message') or '').strip() for row in events]
    if any(not message or len(message) > 2000 for message in messages):
        raise SystemExit('Webhook default messages must contain 1 to 2000 characters')
    if len(messages) != len(set(messages)):
        raise SystemExit('Webhook default messages must be event-specific')
    unsupported = sorted({placeholder for message in messages
                          for placeholder in PLACEHOLDER.findall(message)
                          if placeholder not in SUPPORTED_PLACEHOLDERS})
    if unsupported:
        raise SystemExit('Unsupported webhook placeholders: ' + ', '.join(unsupported))

    # These files were generated duplicates of the source catalog. Remove them
    # so copy-ready documentation has one maintained location.
    if LEGACY_DIRECTORY.is_dir():
        for stale in LEGACY_DIRECTORY.glob('*.txt'):
            stale.unlink()

    sections = [
        '# Discord webhook message templates',
        '',
        'Generated from `spring-api/src/main/reference/webhook-events.json`.',
        '',
        'This is the single copy-ready reference. Runtime defaults and the staff-panel autofill are derived from the same event catalog.',
    ]
    categories: dict[str, list[dict[str, object]]] = {}
    for row in events:
        categories.setdefault(str(row['category']), []).append(row)
    for category in sorted(categories):
        sections += ['', f'## {title(category)}']
        for row in sorted(categories[category], key=lambda item: str(item['key'])):
            message = str(row['default_message']).strip()
            sections += [
                '', f"### `{row['key']}`", '', str(row.get('description') or ''),
                '', '```text', message, '```',
            ]
    content = '\n'.join(sections) + '\n'

    if '--check' in sys.argv:
        if not TARGET.is_file() or TARGET.read_text(encoding='utf-8') != content:
            raise SystemExit('Webhook template reference is stale')
        if LEGACY_DIRECTORY.is_dir() and any(LEGACY_DIRECTORY.glob('*.txt')):
            raise SystemExit('Legacy per-event webhook template files remain')
        if not JAVA_TARGET.is_file() or JAVA_TARGET.read_text(encoding='utf-8') != java_catalog(events):
            raise SystemExit('Generated Java webhook event catalog is stale')
        return

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding='utf-8')
    JAVA_TARGET.write_text(java_catalog(events), encoding='utf-8')


if __name__ == '__main__':
    main()
