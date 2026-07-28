from __future__ import annotations

# Compatibility facade: callers import one stable module while catalog metadata,
# realistic test payloads, and rendered message templates keep separate reasons to change.
from app.modules.admin.services.webhook_event_catalog import EVENT_CATALOG, EVENT_TYPES
from app.modules.admin.services.webhook_event_samples import (
    EVENT_TEST_SAMPLES,
    event_test_sample,
)
from app.modules.admin.services.webhook_message_templates import DEFAULT_MESSAGES

__all__ = [
    "DEFAULT_MESSAGES",
    "EVENT_CATALOG",
    "EVENT_TEST_SAMPLES",
    "EVENT_TYPES",
    "event_test_sample",
]
