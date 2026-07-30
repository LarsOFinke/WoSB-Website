from __future__ import annotations

import ast
from pathlib import Path
import re

from app import create_app
from app.core.config import settings
from app.modules.calendar.constants import FLEET_EVENT_CATEGORY_VALUES
from app.modules.files.services.file_service import ALLOWED_MIME_TYPES
from app.modules.fleet.schemas.constants import (
    FLEET_FOCUS_VALUES,
    FLEET_ROLE_VALUES,
    FLEET_STATUS_VALUES,
)
from app.modules.squads.models.squad_member import SQUAD_ROLES


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SOURCE = REPOSITORY_ROOT / "frontend/src"
HTTP_METHODS = {"get", "post", "put", "delete", "patch"}
CLIENT_METHODS = {
    "get": "get",
    "post": "post",
    "postForm": "post",
    "put": "put",
    "deleteRequest": "delete",
}
API_CALL_PATTERN = re.compile(
    r"\b(?P<client>get|post|postForm|put|deleteRequest)"
    r"\(\s*(?:withQuery\(\s*)?"
    r"(?P<quote>['\"`])(?P<path>/.*?)(?P=quote)"
)
STRING_PATTERN = re.compile(r"['\"]([^'\"]+)['\"]")


def _normalized_path(path: str) -> str:
    path = re.sub(r"\$\{[^}]+}", "{}", path)
    return re.sub(r"{[^}]+}", "{}", path)


def _frontend_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    api_files = sorted(FRONTEND_SOURCE.glob("modules/*/api/*.js"))
    assert api_files, "No frontend API modules found."
    for path in api_files:
        source = path.read_text(encoding="utf-8")
        for match in API_CALL_PATTERN.finditer(source):
            operations.add(
                (
                    CLIENT_METHODS[match.group("client")],
                    _normalized_path(match.group("path")),
                )
            )
    return operations


def _backend_operations() -> set[tuple[str, str]]:
    schema = create_app().openapi()
    operations: set[tuple[str, str]] = set()
    for raw_path, path_item in schema["paths"].items():
        path = raw_path.removeprefix(settings.api_prefix)
        for method in path_item:
            normalized_method = method.lower()
            if normalized_method in HTTP_METHODS:
                operations.add((normalized_method, _normalized_path(path)))
    return operations


def _exported_array(path: Path, name: str) -> tuple[str, ...]:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        rf"export\s+const\s+{re.escape(name)}\s*=\s*\[(?P<body>.*?)]",
        source,
        re.DOTALL,
    )
    assert match is not None, f"Missing frontend contract constant {name} in {path}."
    return tuple(STRING_PATTERN.findall(match.group("body")))


def _exported_integer_expression(path: Path, name: str) -> int:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        rf"export\s+const\s+{re.escape(name)}\s*=\s*(?P<expression>[^\n]+)",
        source,
    )
    assert match is not None, f"Missing frontend contract constant {name} in {path}."
    expression = ast.parse(match.group("expression").strip(), mode="eval")

    def evaluate(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            return left * right
        raise AssertionError(f"Unsupported numeric contract expression: {ast.dump(node)}")

    return evaluate(expression)


def test_every_frontend_api_operation_exists_in_backend_openapi() -> None:
    frontend = _frontend_operations()
    backend = _backend_operations()
    missing = sorted(frontend - backend)
    assert not missing, f"Frontend calls missing backend operations: {missing}"
    assert len(frontend) >= 100, "Unexpectedly few frontend API operations were discovered."


def test_shared_domain_values_match() -> None:
    calendar_api = FRONTEND_SOURCE / "modules/calendar/api/calendar.js"
    fleet_api = FRONTEND_SOURCE / "modules/fleet/api/fleet.js"
    squads_api = FRONTEND_SOURCE / "modules/squads/api/squads.js"

    assert set(_exported_array(calendar_api, "FLEET_EVENT_CATEGORIES")) == FLEET_EVENT_CATEGORY_VALUES
    assert set(_exported_array(fleet_api, "FLEET_FOCUS_VALUES")) == FLEET_FOCUS_VALUES
    assert set(_exported_array(fleet_api, "FLEET_ROLES")) == FLEET_ROLE_VALUES
    assert set(_exported_array(fleet_api, "FLEET_MEMBER_STATUSES")) == FLEET_STATUS_VALUES
    assert set(_exported_array(squads_api, "SQUAD_ROLES")) == SQUAD_ROLES


def test_upload_contract_matches_backend_configuration() -> None:
    file_types = FRONTEND_SOURCE / "modules/files/fileTypes.js"
    frontend_mime_types = set(_exported_array(file_types, "IMAGE_MIME_TYPES"))
    frontend_mime_types.update(_exported_array(file_types, "ACCEPTED_FILE_TYPES"))

    assert frontend_mime_types == ALLOWED_MIME_TYPES
    assert _exported_integer_expression(file_types, "MAX_IMAGE_BYTES") == (
        settings.upload_image_limit_mb * 1024 * 1024
    )
    assert _exported_integer_expression(file_types, "MAX_DOCUMENT_BYTES") == (
        settings.upload_document_limit_mb * 1024 * 1024
    )
    assert _exported_integer_expression(file_types, "MAX_UPLOAD_BYTES") == (
        settings.upload_video_limit_mb * 1024 * 1024
    )
