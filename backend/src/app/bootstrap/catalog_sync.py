from __future__ import annotations

import hashlib
import json
from typing import Any

MASTER_DATA_SEED_REVISION = "2026-07-master-data-v6-json-catalog"
CUSTOM_MASTER_DATA_REVISION = "custom"


def seed_key(namespace: str, *parts: object) -> str:
    normalized = ":".join(str(part).strip().casefold() for part in parts)
    return f"{namespace}:{normalized}"


def seed_checksum(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def should_apply_seed(row: object, *, payload: dict[str, Any]) -> bool:
    if bool(getattr(row, "is_seed_overridden", False)):
        return False
    return (
        getattr(row, "seed_revision", None) != MASTER_DATA_SEED_REVISION
        or getattr(row, "seed_checksum", None) != seed_checksum(payload)
    )


def mark_seed_applied(row: object, *, key: str, payload: dict[str, Any]) -> None:
    setattr(row, "seed_key", key)
    setattr(row, "seed_revision", MASTER_DATA_SEED_REVISION)
    setattr(row, "seed_checksum", seed_checksum(payload))
    setattr(row, "is_seed_overridden", False)
