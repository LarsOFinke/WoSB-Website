#!/usr/bin/env python3
"""Generate typed Spring MVC API interfaces from the reviewed OpenAPI snapshot."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from difflib import unified_diff
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "contracts/api-contract.json").read_text(encoding="utf-8"))
TARGET = ROOT / "spring-api/src/main/java/eu/royalblackwater/api/contract/api"
PACKAGE = "eu.royalblackwater.api.contract.api"
HTTP = {
    "get": "GetMapping",
    "post": "PostMapping",
    "put": "PutMapping",
    "patch": "PatchMapping",
    "delete": "DeleteMapping",
}

JAVA_KEYWORDS = {
    "class", "default", "protected", "public", "private", "record", "switch", "case", "new",
    "return", "void", "long", "int", "double", "boolean", "null", "true", "false", "this",
    "super", "interface", "enum", "extends", "implements", "package", "import", "static", "final",
    "try", "catch", "finally", "throw", "throws", "while", "for", "if", "else", "do", "break",
    "continue", "instanceof", "var", "yield", "sealed", "permits",
}


def camel(value: str, upper: bool = False) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    if not parts:
        return "value"
    first = parts[0][:1].upper() + parts[0][1:] if upper else parts[0].lower()
    name = first + "".join(part[:1].upper() + part[1:] for part in parts[1:])
    return name + "Value" if name in JAVA_KEYWORDS else name


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def java_type(schema: dict, required: bool) -> tuple[str, set[str]]:
    imports: set[str] = set()
    if "$ref" in schema:
        name = ref_name(schema["$ref"])
        imports.add(f"eu.royalblackwater.api.dto.{name}")
        return name, imports
    if "anyOf" in schema:
        choices = [entry for entry in schema["anyOf"] if entry.get("type") != "null"]
        if not choices:
            return "Object", imports
        resolved = [java_type(entry, False) for entry in choices]
        for _, nested in resolved:
            imports.update(nested)
        names = {name for name, _ in resolved}
        if len(names) == 1:
            return resolved[0][0], imports
        if names <= {"Long", "Double", "Number"}:
            return "Number", imports
        return "Object", imports
    kind = schema.get("type")
    fmt = schema.get("format")
    if kind == "string":
        if fmt == "binary":
            imports.add("org.springframework.core.io.Resource")
            return "Resource", imports
        if fmt == "date":
            imports.add("java.time.LocalDate")
            return "LocalDate", imports
        if fmt == "date-time":
            imports.add("java.time.LocalDateTime")
            return "LocalDateTime", imports
        return "String", imports
    if kind == "integer":
        return ("long" if required else "Long"), imports
    if kind == "number":
        return ("double" if required else "Double"), imports
    if kind == "boolean":
        return ("boolean" if required else "Boolean"), imports
    if kind == "array":
        inner, nested = java_type(schema.get("items", {}), True)
        imports.update(nested)
        imports.add("java.util.List")
        boxed = {"long": "Long", "double": "Double", "boolean": "Boolean"}.get(inner, inner)
        return f"List<{boxed}>", imports
    if kind == "object" or "additionalProperties" in schema:
        imports.add("java.util.Map")
        return "Map<String, Object>", imports
    return "Object", imports


def group_for(path: str) -> str:
    parts = [part for part in path.removeprefix("/api/").split("/") if not part.startswith("{")]
    if not parts:
        return "root"
    if parts[0] == "admin" and len(parts) > 1:
        return "admin-" + parts[1]
    if parts[0] == "calendar" and len(parts) > 1 and parts[1] == "raid-helper":
        return "calendar-raid-helper"
    return parts[0]


def request_body(operation: dict) -> tuple[str | None, bool, set[str]]:
    body = operation.get("requestBody", {})
    content = body.get("content", {})
    imports: set[str] = set()
    if "application/json" in content:
        body_type, nested = java_type(content["application/json"].get("schema", {}), True)
        imports.update(nested)
        return body_type, False, imports
    if "multipart/form-data" in content:
        schema = content["multipart/form-data"].get("schema", {})
        if "$ref" in schema:
            definition = SCHEMA["components"]["schemas"].get(ref_name(schema["$ref"]), {})
            properties = definition.get("properties", {})
            upload_name = next(iter(properties), "file")
        else:
            upload_name = next(iter(schema.get("properties", {})), "file")
        return upload_name, True, imports
    return None, False, imports


def success_status(operation: dict) -> int:
    codes = [int(code) for code in operation.get("responses", {}) if code.isdigit() and 200 <= int(code) < 300]
    return min(codes) if codes else 200


def success_response_type(operation: dict) -> tuple[str, set[str]]:
    status = success_status(operation)
    response = operation.get("responses", {}).get(str(status), {})
    if status == 204:
        return "Void", set()
    content = response.get("content", {})
    if not content:
        return "Void", set()
    media = "application/json" if "application/json" in content else next(iter(content))
    schema = content[media].get("schema", {})
    return java_type(schema, True)


def method_name(operation_id: str, used: set[str]) -> str:
    base = camel(operation_id.split("_api_", 1)[0])
    name = base
    if name in used:
        name += hashlib.sha1(operation_id.encode()).hexdigest()[:6]
    used.add(name)
    return name


def parameter_annotation(parameter: dict) -> tuple[str, str, str, set[str]]:
    raw = parameter["name"]
    location = parameter["in"]
    required = bool(parameter.get("required"))
    schema = parameter.get("schema", {})
    value_type, imports = java_type(schema, True if "default" in schema else required)
    name = camel(raw)
    if location == "path":
        annotation = f'@PathVariable("{raw}")'
        imports.add("org.springframework.web.bind.annotation.PathVariable")
    elif location == "query":
        default = schema.get("default")
        pieces = [f'name = "{raw}"']
        if default is not None:
            default_text = str(default).lower() if isinstance(default, bool) else str(default)
            pieces.append(f'defaultValue = "{default_text.replace(chr(34), chr(92) + chr(34))}"')
        else:
            pieces.append(f"required = {str(required).lower()}")
        annotation = "@RequestParam(" + ", ".join(pieces) + ")"
        imports.add("org.springframework.web.bind.annotation.RequestParam")
        temporal_schema = next((entry for entry in schema.get("anyOf", []) if entry.get("type") != "null"), schema)
        temporal_format = temporal_schema.get("format")
        if temporal_format in {"date", "date-time"}:
            iso = "DATE_TIME" if temporal_format == "date-time" else "DATE"
            annotation = f"@DateTimeFormat(iso = DateTimeFormat.ISO.{iso}) " + annotation
            imports.add("org.springframework.format.annotation.DateTimeFormat")
    else:
        raise ValueError(location)
    return annotation, value_type, name, imports


def operation_signature(operation: dict) -> tuple[list[str], list[tuple[str, str]], str | None, bool, set[str]]:
    signature: list[str] = []
    parameters: list[tuple[str, str]] = []
    imports: set[str] = set()
    for parameter in operation.get("parameters", []):
        if parameter.get("in") == "cookie":
            continue
        annotation, value_type, name, nested = parameter_annotation(parameter)
        imports.update(nested)
        signature.append(f"            {annotation} {value_type} {name}")
        parameters.append((parameter["name"], name))
    body_type, multipart, nested = request_body(operation)
    imports.update(nested)
    if body_type is not None and multipart:
        imports.update({"org.springframework.web.bind.annotation.RequestPart", "org.springframework.web.multipart.MultipartFile"})
        signature.append(f'            @RequestPart("{body_type}") MultipartFile upload')
    elif body_type is not None:
        imports.update({"jakarta.validation.Valid", "org.springframework.web.bind.annotation.RequestBody"})
        signature.append(f"            @Valid @RequestBody {body_type} body")
    return signature, parameters, body_type, multipart, imports


def generate_api(group: str, operations: list[tuple[str, str, dict]]) -> tuple[str, str]:
    class_name = camel(group, upper=True) + "Api"
    imports = {"org.springframework.http.ResponseEntity"}
    methods: list[str] = []
    used: set[str] = set()
    for path, http_method, operation in operations:
        mapping = HTTP[http_method]
        imports.add(f"org.springframework.web.bind.annotation.{mapping}")
        signature, _, _, _, nested = operation_signature(operation)
        imports.update(nested)
        response_type, response_imports = success_response_type(operation)
        imports.update(response_imports)
        signature_text = ",\n".join(signature)
        method = method_name(operation["operationId"], used)
        declaration = (
            f"    ResponseEntity<{response_type}> {method}(\n{signature_text}\n    );\n"
            if signature
            else f"    ResponseEntity<{response_type}> {method}();\n"
        )
        methods.append(f'    @{mapping}("{path}")\n' + declaration)
    import_block = "".join(f"import {value};\n" for value in sorted(imports))
    text = (
        "// Generated by infrastructure/scripts/generation/generate_spring_routes.py; do not edit manually.\n"
        f"package {PACKAGE};\n\n{import_block}\n"
        f"public interface {class_name} {{\n"
        + "\n".join(methods)
        + "}\n"
    )
    return class_name, text


def render_outputs() -> tuple[dict[Path, str], int]:
    grouped: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)
    operation_count = 0
    for path, item in SCHEMA["paths"].items():
        for method, operation in item.items():
            if method not in HTTP:
                continue
            grouped[group_for(path)].append((path, method, operation))
            operation_count += 1
    outputs: dict[Path, str] = {}
    for group, operations in sorted(grouped.items()):
        class_name, text = generate_api(group, sorted(operations))
        outputs[TARGET / f"{class_name}.java"] = text
    return outputs, operation_count


def check_outputs(outputs: dict[Path, str], operation_count: int) -> None:
    expected = set(outputs)
    stale = sorted(set(TARGET.glob("*.java")) - expected) if TARGET.exists() else []
    mismatches: list[str] = []
    for path, generated in outputs.items():
        actual = path.read_text(encoding="utf-8") if path.is_file() else ""
        if actual == generated:
            continue
        diff = unified_diff(actual.splitlines(), generated.splitlines(), fromfile=str(path.relative_to(ROOT)),
                            tofile=f"generated:{path.relative_to(ROOT)}", lineterm="", n=2)
        mismatches.append("\n".join(list(diff)[:40]))
    if stale:
        mismatches.append("stale generated API interfaces: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))
    if mismatches:
        raise SystemExit(
            "[spring-routes] generated API interfaces are stale; run "
            "python3 infrastructure/scripts/generation/generate_spring_routes.py\n" + "\n\n".join(mismatches[:5])
        )
    print(f"Spring API interface generation OK ({len(expected)} interfaces, {operation_count} operations).")


def main() -> None:
    outputs, operation_count = render_outputs()
    if sys.argv[1:] == ["--check"]:
        check_outputs(outputs, operation_count)
        return
    if sys.argv[1:]:
        raise SystemExit("Usage: generate_spring_routes.py [--check]")
    TARGET.mkdir(parents=True, exist_ok=True)
    for path, generated in outputs.items():
        path.write_text(generated, encoding="utf-8")
    for path in TARGET.glob("*.java"):
        if path not in outputs:
            path.unlink()
    print(f"generated {len(outputs)} API interfaces for {operation_count} operations")


if __name__ == "__main__":
    main()
