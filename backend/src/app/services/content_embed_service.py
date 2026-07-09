import re
from collections.abc import Iterable

from app.models import StoredFile

EMBED_PATTERN = re.compile(r"\[\[file:(?P<file_id>\d+)(?:\|(?P<size>[a-z0-9_-]+))?\]\]", re.IGNORECASE)
ALLOWED_EMBED_SIZES = {"small", "medium", "large", "full"}
MAX_INLINE_EMBEDS = 24


class ContentEmbedValidationError(ValueError):
    pass


def parse_embedded_file_ids(body: str) -> list[int]:
    ids: list[int] = []
    for match in EMBED_PATTERN.finditer(body or ""):
        file_id = int(match.group("file_id"))
        if file_id not in ids:
            ids.append(file_id)
    return ids


def validate_content_embeds(body: str, files: Iterable[StoredFile]) -> None:
    available_file_ids = {file.id for file in files}
    referenced_file_ids: list[int] = []

    for match in EMBED_PATTERN.finditer(body or ""):
        referenced_file_ids.append(int(match.group("file_id")))
        size = (match.group("size") or "large").lower()
        if size not in ALLOWED_EMBED_SIZES:
            allowed = ", ".join(sorted(ALLOWED_EMBED_SIZES))
            raise ContentEmbedValidationError(f"Invalid inline file size '{size}'. Allowed: {allowed}.")

    if len(referenced_file_ids) > MAX_INLINE_EMBEDS:
        raise ContentEmbedValidationError(f"Too many inline file embeds. Maximum is {MAX_INLINE_EMBEDS}.")

    missing = [file_id for file_id in referenced_file_ids if file_id not in available_file_ids]
    if missing:
        raise ContentEmbedValidationError("Inline file embeds must reference files attached to the same post or guide.")
