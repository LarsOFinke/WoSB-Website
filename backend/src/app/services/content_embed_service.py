import re
from collections.abc import Iterable

from app.models import Build, StoredFile

FILE_EMBED_PATTERN = re.compile(r"\[\[file:(?P<file_id>\d+)(?:\|(?P<size>[a-z0-9_-]+))?\]\]", re.IGNORECASE)
BUILD_EMBED_PATTERN = re.compile(r"\[\[build:(?P<build_id>\d+)(?:\|(?P<layout>[a-z0-9_-]+))?\]\]", re.IGNORECASE)
ALLOWED_EMBED_SIZES = {"small", "medium", "large", "full"}
ALLOWED_BUILD_EMBED_LAYOUTS = {"compact", "card", "full"}
MAX_INLINE_EMBEDS = 24
MAX_INLINE_BUILD_EMBEDS = 16


class ContentEmbedValidationError(ValueError):
    pass


def _unique_ordered(values: Iterable[int]) -> list[int]:
    ids: list[int] = []
    for value in values:
        if value not in ids:
            ids.append(value)
    return ids


def parse_embedded_file_ids(body: str) -> list[int]:
    return _unique_ordered(int(match.group("file_id")) for match in FILE_EMBED_PATTERN.finditer(body or ""))


def parse_embedded_build_ids(body: str) -> list[int]:
    return _unique_ordered(int(match.group("build_id")) for match in BUILD_EMBED_PATTERN.finditer(body or ""))


def validate_content_embeds(body: str, files: Iterable[StoredFile]) -> None:
    available_file_ids = {file.id for file in files}
    referenced_file_ids: list[int] = []

    for match in FILE_EMBED_PATTERN.finditer(body or ""):
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


def validate_build_embeds(body: str, builds: Iterable[Build]) -> None:
    available_build_ids = {build.id for build in builds}
    referenced_build_ids: list[int] = []

    for match in BUILD_EMBED_PATTERN.finditer(body or ""):
        referenced_build_ids.append(int(match.group("build_id")))
        layout = (match.group("layout") or "card").lower()
        if layout not in ALLOWED_BUILD_EMBED_LAYOUTS:
            allowed = ", ".join(sorted(ALLOWED_BUILD_EMBED_LAYOUTS))
            raise ContentEmbedValidationError(f"Invalid inline build layout '{layout}'. Allowed: {allowed}.")

    if len(referenced_build_ids) > MAX_INLINE_BUILD_EMBEDS:
        raise ContentEmbedValidationError(f"Too many inline build embeds. Maximum is {MAX_INLINE_BUILD_EMBEDS}.")

    missing = [build_id for build_id in referenced_build_ids if build_id not in available_build_ids]
    if missing:
        raise ContentEmbedValidationError("Inline build embeds must reference builds linked to the same guide.")
