from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


class JsonSafeEncoder:
    def convert(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, (Decimal, UUID, Path, Enum)):
            return str(value.value if isinstance(value, Enum) else value)
        if isinstance(value, dict):
            return {str(key): self.convert(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self.convert(item) for item in value]
        raise TypeError(
            "Unsupported webhook payload type "
            f"{type(value).__module__}.{type(value).__qualname__}; "
            "publish a Pydantic response model or a JSON-compatible mapping instead."
        )
