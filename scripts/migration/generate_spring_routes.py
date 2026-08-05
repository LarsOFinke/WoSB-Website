#!/usr/bin/env python3
"""Generate Spring MVC route adapters from the reviewed OpenAPI snapshot."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts/api-contract.json").read_text(encoding="utf-8"))
TARGET = ROOT / "spring-api/src/main/java/eu/royalblackwater/api/transport/generated"
PACKAGE = "eu.royalblackwater.api.transport.generated"
HTTP = {"get": "GetMapping", "post": "PostMapping", "put": "PutMapping", "patch": "PatchMapping", "delete": "DeleteMapping"}

JAVA_KEYWORDS = {"class", "default", "protected", "public", "private", "record", "switch", "case", "new", "return", "void", "long", "int", "double", "boolean", "null", "true", "false", "this", "super", "interface", "enum", "extends", "implements", "package", "import", "static", "final", "try", "catch", "finally", "throw", "throws", "while", "for", "if", "else", "do", "break", "continue", "instanceof", "var", "yield", "sealed", "permits"}


def camel(value: str, upper: bool = False) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", value) if p]
    if not parts:
        return "value"
    first = parts[0][:1].upper() + parts[0][1:] if upper else parts[0].lower()
    name = first + "".join(part[:1].upper() + part[1:] for part in parts[1:])
    if name in JAVA_KEYWORDS:
        name += "Value"
    return name


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def java_type(schema: dict, required: bool) -> tuple[str, set[str]]:
    imports: set[str] = set()
    if "$ref" in schema:
        name = ref_name(schema["$ref"])
        imports.add(f"eu.royalblackwater.api.contract.{name}")
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
        return f"List<{ {'long':'Long','double':'Double','boolean':'Boolean'}.get(inner, inner) }>", imports
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


def method_name(operation_id: str, used: set[str]) -> str:
    base = camel(operation_id.split("_api_", 1)[0])
    name = base
    if name in used:
        name += hashlib.sha1(operation_id.encode()).hexdigest()[:6]
    used.add(name)
    return name


def mapping_path(path: str, group: str) -> str:
    # Controllers intentionally use full paths so generated groups can be moved without changing contracts.
    return path


def parameter_annotation(parameter: dict) -> tuple[str, str, str, set[str]]:
    raw = parameter["name"]
    location = parameter["in"]
    required = bool(parameter.get("required"))
    schema = parameter.get("schema", {})
    if "default" in schema:
        required_for_type = True
    else:
        required_for_type = required
    value_type, imports = java_type(schema, required_for_type)
    name = camel(raw)
    if location == "path":
        annotation = f'@PathVariable("{raw}")'
        imports.add("org.springframework.web.bind.annotation.PathVariable")
    elif location == "query":
        default = schema.get("default")
        pieces = [f'name = "{raw}"']
        if default is not None:
            default_text = str(default).lower() if isinstance(default, bool) else str(default)
            escaped = default_text.replace('"', '\\"')
            pieces.append(f'defaultValue = "{escaped}"')
        else:
            pieces.append(f"required = {str(required).lower()}")
        annotation = "@RequestParam(" + ", ".join(pieces) + ")"
        imports.add("org.springframework.web.bind.annotation.RequestParam")
        temporal_schema = next(
            (entry for entry in schema.get("anyOf", []) if entry.get("type") != "null"),
            schema,
        )
        temporal_format = temporal_schema.get("format")
        if temporal_format in {"date", "date-time"}:
            iso = "DATE_TIME" if temporal_format == "date-time" else "DATE"
            annotation = f"@DateTimeFormat(iso = DateTimeFormat.ISO.{iso}) " + annotation
            imports.add("org.springframework.format.annotation.DateTimeFormat")
    else:
        raise ValueError(location)
    return annotation, value_type, name, imports


def generate_controller(group: str, operations: list[tuple[str, str, dict]]) -> tuple[str, str]:
    class_name = camel(group, upper=True) + "GeneratedController"
    imports = {
        "eu.royalblackwater.api.transport.ApiOperationDispatcher",
        "eu.royalblackwater.api.transport.ApiParameters",
        "org.springframework.http.ResponseEntity",
        "org.springframework.validation.annotation.Validated",
        "org.springframework.web.bind.annotation.RestController",
    }
    methods: list[str] = []
    used: set[str] = set()
    for path, http_method, operation in operations:
        mapping = HTTP[http_method]
        imports.add(f"org.springframework.web.bind.annotation.{mapping}")
        signature: list[str] = []
        arguments: list[str] = []
        for parameter in operation.get("parameters", []):
            if parameter.get("in") == "cookie":
                continue
            annotation, value_type, name, nested = parameter_annotation(parameter)
            imports.update(nested)
            signature.append(f"            {annotation} {value_type} {name}")
            arguments.extend([f'"{parameter["name"]}"', name])
        body_type, multipart, nested = request_body(operation)
        imports.update(nested)
        body_expr = "null"
        file_expr = "null"
        if body_type is not None and multipart:
            imports.update({"org.springframework.web.bind.annotation.RequestPart", "org.springframework.web.multipart.MultipartFile"})
            signature.append(f'            @RequestPart("{body_type}") MultipartFile upload')
            file_expr = "upload"
        elif body_type is not None:
            imports.update({"jakarta.validation.Valid", "org.springframework.web.bind.annotation.RequestBody"})
            signature.append(f"            @Valid @RequestBody {body_type} body")
            body_expr = "body"
        params_expr = "ApiParameters.empty()" if not arguments else "ApiParameters.of(" + ", ".join(arguments) + ")"
        signature_text = ",\n".join(signature)
        method = method_name(operation["operationId"], used)
        status = success_status(operation)
        methods.append(
            f'    @{mapping}("{mapping_path(path, group)}")\n'
            f"    public ResponseEntity<?> {method}(\n{signature_text}\n    ) {{\n"
            f'        return dispatcher.dispatch("{operation["operationId"]}", {params_expr}, {body_expr}, {file_expr}, {status});\n'
            "    }\n"
        )
    import_block = "".join(f"import {value};\n" for value in sorted(imports))
    text = (
        "// Generated by scripts/migration/generate_spring_routes.py; do not edit manually.\n"
        f"package {PACKAGE};\n\n{import_block}\n"
        "@RestController\n@Validated\n"
        f"public class {class_name} {{\n"
        "    private final ApiOperationDispatcher dispatcher;\n\n"
        f"    public {class_name}(ApiOperationDispatcher dispatcher) {{\n"
        "        this.dispatcher = dispatcher;\n"
        "    }\n\n"
        + "\n".join(methods)
        + "}\n"
    )
    return class_name, text


def main() -> None:
    grouped: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)
    operation_ids: list[str] = []
    for path, item in SCHEMA["paths"].items():
        for method, operation in item.items():
            if method not in HTTP:
                continue
            grouped[group_for(path)].append((path, method, operation))
            operation_ids.append(operation["operationId"])
    TARGET.mkdir(parents=True, exist_ok=True)
    expected = set()
    for group, operations in sorted(grouped.items()):
        class_name, text = generate_controller(group, sorted(operations))
        filename = class_name + ".java"
        (TARGET / filename).write_text(text, encoding="utf-8")
        expected.add(filename)
    for path in TARGET.glob("*.java"):
        if path.name not in expected:
            path.unlink()
    catalog = ROOT / "spring-api/src/main/java/eu/royalblackwater/api/transport/ApiOperationCatalog.java"
    values = ",\n".join(f'            "{operation_id}"' for operation_id in sorted(operation_ids))
    catalog.write_text(
        "// Generated by scripts/migration/generate_spring_routes.py; do not edit manually.\n"
        "package eu.royalblackwater.api.transport;\n\n"
        "import java.util.Set;\n\n"
        "public final class ApiOperationCatalog {\n"
        "    private ApiOperationCatalog() { }\n"
        "    public static final Set<String> ALL = Set.of(\n"
        + values + "\n    );\n}\n",
        encoding="utf-8",
    )
    print(f"generated {len(grouped)} controllers for {len(operation_ids)} operations")


if __name__ == "__main__":
    main()
