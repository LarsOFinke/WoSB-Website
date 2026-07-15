from __future__ import annotations

from datetime import datetime
from typing import Any


class JsonSafeEncoder:
    def convert(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): self.convert(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self.convert(item) for item in value]
        return value
