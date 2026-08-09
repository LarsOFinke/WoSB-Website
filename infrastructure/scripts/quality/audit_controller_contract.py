#!/usr/bin/env python3
"""Verify that controller-owned Spring bindings match the reviewed OpenAPI specification."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OPENAPI = ROOT / "openapi/openapi.json"
CONTROLLERS = ROOT / "spring-api/src/main/java/eu/royalblackwater/api"
HTTP = {"get": "Get", "post": "Post", "put": "Put", "patch": "Patch", "delete": "Delete"}
JAVA_KEYWORDS = {
    "class", "default", "protected", "public", "private", "record", "switch", "case", "new",
    "return", "void", "long", "int", "double", "boolean", "null", "true", "false", "this",
    "super", "interface", "enum", "extends", "implements", "package", "import", "static", "final",
    "try", "catch", "finally", "throw", "throws", "while", "for", "if", "else", "do", "break",
    "continue", "instanceof", "var", "yield", "sealed", "permits",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[controller-contract] {message}")


def camel(value: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    if not parts:
        return "value"
    name = parts[0].lower() + "".join(part[:1].upper() + part[1:] for part in parts[1:])
    return name + "Value" if name in JAVA_KEYWORDS else name


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def java_type(schema: dict, required: bool) -> str:
    if "$ref" in schema:
        return ref_name(schema["$ref"])
    if "anyOf" in schema:
        choices = [entry for entry in schema["anyOf"] if entry.get("type") != "null"]
        if not choices:
            return "Object"
        names = {java_type(entry, False) for entry in choices}
        if len(names) == 1:
            return next(iter(names))
        if names <= {"Long", "Double", "Number"}:
            return "Number"
        return "Object"
    kind = schema.get("type")
    fmt = schema.get("format")
    if kind == "string":
        if fmt == "binary":
            return "Resource"
        if fmt == "date":
            return "LocalDate"
        if fmt == "date-time":
            return "LocalDateTime"
        return "String"
    if kind == "integer":
        return "long" if required else "Long"
    if kind == "number":
        return "double" if required else "Double"
    if kind == "boolean":
        return "boolean" if required else "Boolean"
    if kind == "array":
        inner = java_type(schema.get("items", {}), True)
        boxed = {"long": "Long", "double": "Double", "boolean": "Boolean"}.get(inner, inner)
        return f"List<{boxed}>"
    if kind == "object" or "additionalProperties" in schema:
        return "Map<String, Object>"
    return "Object"


def success_status(operation: dict) -> int:
    values = [int(code) for code in operation.get("responses", {}) if code.isdigit() and 200 <= int(code) < 300]
    return min(values) if values else 200


def response_type(operation: dict) -> str:
    status = success_status(operation)
    response = operation.get("responses", {}).get(str(status), {})
    if status == 204:
        return "Void"
    content = response.get("content", {})
    if not content:
        return "Void"
    media = "application/json" if "application/json" in content else next(iter(content))
    return java_type(content[media].get("schema", {}), True)


def group_for(path: str) -> str:
    parts = [part for part in path.removeprefix("/api/").split("/") if not part.startswith("{")]
    if not parts:
        return "root"
    if parts[0] == "admin" and len(parts) > 1:
        return "admin-" + parts[1]
    if parts[0] == "calendar" and len(parts) > 1 and parts[1] == "raid-helper":
        return "calendar-raid-helper"
    return parts[0]


def expected_method(operation_id: str, used: set[str]) -> str:
    base = camel(operation_id.split("_api_", 1)[0])
    name = base
    if name in used:
        name += hashlib.sha1(operation_id.encode()).hexdigest()[:6]
    used.add(name)
    return name


def normalize(value: str) -> str:
    return " ".join(value.split())


def expected_parameter(parameter: dict) -> str:
    raw = parameter["name"]
    location = parameter["in"]
    required = bool(parameter.get("required"))
    schema = parameter.get("schema", {})
    value_type = java_type(schema, True if "default" in schema else required)
    name = camel(raw)
    if location == "path":
        return f'@PathVariable("{raw}") {value_type} {name}'
    if location == "header":
        return f'@RequestHeader("{raw}") {value_type} {name}'
    if location != "query":
        raise ValueError(location)
    default = schema.get("default")
    pieces = [f'name = "{raw}"']
    if default is not None:
        default_text = str(default).lower() if isinstance(default, bool) else str(default)
        pieces.append(f'defaultValue = "{default_text}"')
    else:
        pieces.append(f"required = {str(required).lower()}")
    annotation = "@RequestParam(" + ", ".join(pieces) + ")"
    temporal_schema = next((entry for entry in schema.get("anyOf", []) if entry.get("type") != "null"), schema)
    temporal_format = temporal_schema.get("format")
    if temporal_format in {"date", "date-time"}:
        iso = "DATE_TIME" if temporal_format == "date-time" else "DATE"
        annotation = f"@DateTimeFormat(iso = DateTimeFormat.ISO.{iso}) " + annotation
    return f"{annotation} {value_type} {name}"


def expected_body(document: dict, operation: dict) -> tuple[str | None, bool]:
    content = operation.get("requestBody", {}).get("content", {})
    if "application/json" in content:
        return java_type(content["application/json"].get("schema", {}), True), False
    if "multipart/form-data" in content:
        schema = content["multipart/form-data"].get("schema", {})
        if "$ref" in schema:
            definition = document["components"]["schemas"].get(ref_name(schema["$ref"]), {})
            upload_name = next(iter(definition.get("properties", {})), "file")
        else:
            upload_name = next(iter(schema.get("properties", {})), "file")
        return upload_name, True
    return None, False


def main() -> None:
    document = json.loads(OPENAPI.read_text(encoding="utf-8"))
    controller_files = sorted(CONTROLLERS.glob("*/controller/*Controller.java"))
    require(controller_files, "no module controllers found")

    actual: dict[tuple[str, str], tuple[Path, str, str, str, str]] = {}
    method_pattern = re.compile(
        r"@(Get|Post|Put|Patch|Delete)Mapping\(([^\n]+)\)\s+"
        r"public\s+ResponseEntity<([^\n]+)>\s+(\w+)\((.*?)\)\s*\{",
        re.S,
    )
    for path in controller_files:
        source = path.read_text(encoding="utf-8")
        require("implements " not in re.search(r"public class[^\{]+", source).group(0),
                f"controller still implements a generated transport interface: {path.relative_to(ROOT)}")
        for match in method_pattern.finditer(source):
            verb, mapping_args, response, method, params = match.groups()
            path_match = re.search(r'"([^"]+)"', mapping_args)
            require(path_match is not None, f"mapping has no literal path in {path.relative_to(ROOT)}: {method}")
            key = (verb.lower(), path_match.group(1))
            require(key not in actual, f"duplicate controller route: {key[0].upper()} {key[1]}")
            actual[key] = (path, method, normalize(response), normalize(params), mapping_args)

    expected_count = 0
    used_by_group: dict[str, set[str]] = defaultdict(set)
    for route, path_item in document["paths"].items():
        for verb, operation in path_item.items():
            if verb not in HTTP or not isinstance(operation, dict):
                continue
            expected_count += 1
            key = (verb, route)
            require(key in actual, f"missing controller route: {verb.upper()} {route}")
            source_path, method, actual_response, actual_params, mapping_args = actual[key]
            operation_id = operation["operationId"]
            expected_name = expected_method(operation_id, used_by_group[group_for(route)])
            require(method == expected_name,
                    f"method drift for {verb.upper()} {route}: expected {expected_name}, got {method}")
            expected_response = response_type(operation)
            require(actual_response == expected_response,
                    f"response type drift for {verb.upper()} {route}: expected {expected_response}, got {actual_response}")
            for parameter in operation.get("parameters", []):
                if parameter.get("in") == "cookie":
                    continue
                snippet = normalize(expected_parameter(parameter))
                require(snippet in actual_params,
                        f"parameter binding drift for {verb.upper()} {route}: missing `{snippet}` in {source_path.relative_to(ROOT)}")
            body, multipart = expected_body(document, operation)
            if body is not None and multipart:
                snippet = normalize(f'@RequestPart("{body}") MultipartFile upload')
                require(snippet in actual_params,
                        f"multipart binding drift for {verb.upper()} {route}: expected `{snippet}`")
                require("MediaType.MULTIPART_FORM_DATA_VALUE" in mapping_args,
                        f"multipart route lacks explicit consumes binding: {verb.upper()} {route}")
            elif body is not None:
                snippet = normalize(f"@Valid @RequestBody {body} body")
                require(snippet in actual_params,
                        f"request DTO binding drift for {verb.upper()} {route}: expected `{snippet}`")

    require(len(actual) == expected_count,
            f"controller route count differs from OpenAPI: controllers={len(actual)}, openapi={expected_count}")
    print(f"Controller/OpenAPI contract OK ({expected_count} operations, {len(controller_files)} controllers).")


if __name__ == "__main__":
    main()
