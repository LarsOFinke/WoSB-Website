#!/usr/bin/env python3
"""Generate immutable Java API records from the reviewed API contract."""
from __future__ import annotations

import json
import keyword
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts/api-contract.json"
TARGET = ROOT / "spring-api/src/main/java/eu/royalblackwater/api/contract"
PACKAGE = "eu.royalblackwater.api.contract"


def java_name(value: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", value)
    name = parts[0].lower() + "".join(part[:1].upper() + part[1:] for part in parts[1:] if part)
    if not name:
        name = "value"
    java_keywords = {"abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const", "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float", "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native", "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp", "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void", "volatile", "while", "record", "sealed", "permits", "yield", "var", "null", "true", "false"}
    if keyword.iskeyword(name) or name in java_keywords:
        name += "Value"
    return name


def ref_name(value: str) -> str:
    return value.rsplit("/", 1)[-1]


def schema_type(schema: dict, required: bool = True) -> tuple[str, set[str]]:
    imports: set[str] = set()
    if "$ref" in schema:
        return ref_name(schema["$ref"]), imports
    if "anyOf" in schema:
        choices = [entry for entry in schema["anyOf"] if entry.get("type") != "null"]
        if not choices:
            return "Object", imports
        resolved = [schema_type(entry, required=False) for entry in choices]
        imports.update(*(item[1] for item in resolved))
        names = {item[0] for item in resolved}
        if len(names) == 1:
            return resolved[0][0], imports
        if names <= {"Long", "Double", "Number"}:
            return "Number", imports
        return "Object", imports
    value_type = schema.get("type")
    fmt = schema.get("format")
    nullable = not required
    if value_type == "string":
        if fmt == "date-time":
            imports.add("java.time.LocalDateTime")
            return "LocalDateTime", imports
        if fmt == "date":
            imports.add("java.time.LocalDate")
            return "LocalDate", imports
        if fmt == "binary":
            return "byte[]", imports
        return "String", imports
    if value_type == "integer":
        return ("Long" if nullable else "long"), imports
    if value_type == "number":
        return ("Double" if nullable else "double"), imports
    if value_type == "boolean":
        return ("Boolean" if nullable else "boolean"), imports
    if value_type == "array":
        inner, nested = schema_type(schema.get("items", {}), required=True)
        imports.update(nested)
        imports.add("java.util.List")
        return f"List<{boxed(inner)}>", imports
    if value_type == "object" or "additionalProperties" in schema:
        additional = schema.get("additionalProperties", True)
        inner = "Object"
        if isinstance(additional, dict):
            inner, nested = schema_type(additional, required=False)
            imports.update(nested)
        imports.add("java.util.Map")
        return f"Map<String, {boxed(inner)}>", imports
    return "Object", imports


def boxed(value: str) -> str:
    return {"long": "Long", "double": "Double", "boolean": "Boolean", "int": "Integer"}.get(value, value)


def annotations(schema: dict, required: bool) -> tuple[list[str], set[str]]:
    values: list[str] = []
    imports: set[str] = set()
    if required and schema.get("type") not in {"boolean", "integer", "number"} and not schema.get("anyOf"):
        values.append("@NotNull")
        imports.add("jakarta.validation.constraints.NotNull")
    minimum = schema.get("minimum")
    if minimum is not None and float(minimum).is_integer():
        values.append(f"@Min({int(minimum)})")
        imports.add("jakarta.validation.constraints.Min")
    maximum = schema.get("maximum")
    if maximum is not None and float(maximum).is_integer():
        values.append(f"@Max({int(maximum)})")
        imports.add("jakarta.validation.constraints.Max")
    min_length = schema.get("minLength")
    max_length = schema.get("maxLength")
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    if any(value is not None for value in (min_length, max_length, min_items, max_items)):
        args = []
        minimum_size = min_length if min_length is not None else min_items
        maximum_size = max_length if max_length is not None else max_items
        if minimum_size is not None:
            args.append(f"min = {int(minimum_size)}")
        if maximum_size is not None:
            args.append(f"max = {int(maximum_size)}")
        values.append("@Size(" + ", ".join(args) + ")")
        imports.add("jakarta.validation.constraints.Size")
    pattern = schema.get("pattern")
    if pattern:
        escaped = pattern.replace("\\", "\\\\").replace('"', '\\"')
        values.append(f'@Pattern(regexp = "{escaped}")')
        imports.add("jakarta.validation.constraints.Pattern")
    return values, imports


def generate_record(name: str, schema: dict) -> str:
    required = set(schema.get("required", []))
    imports: set[str] = set()
    components: list[str] = []
    for raw_name, prop in schema.get("properties", {}).items():
        is_required = raw_name in required
        value_type, type_imports = schema_type(prop, required=is_required)
        field_annotations, annotation_imports = annotations(prop, is_required)
        imports.update(type_imports)
        imports.update(annotation_imports)
        prefix = " ".join(field_annotations)
        if prefix:
            prefix += " "
        components.append(f"        {prefix}{value_type} {java_name(raw_name)}")
    imports_block = "".join(f"import {value};\n" for value in sorted(imports))
    if components:
        body = ",\n".join(components)
        declaration = f"public record {name}(\n{body}) {{ }}\n"
    else:
        declaration = f"public record {name}() {{ }}\n"
    return (
        "// Generated by scripts/migration/generate_java_contracts.py; do not edit manually.\n"
        f"package {PACKAGE};\n\n"
        + (imports_block + "\n" if imports_block else "")
        + declaration
    )


def main() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    definitions = schema["components"]["schemas"]
    TARGET.mkdir(parents=True, exist_ok=True)
    expected = set()
    for name, definition in sorted(definitions.items()):
        path = TARGET / f"{name}.java"
        path.write_text(generate_record(name, definition), encoding="utf-8")
        expected.add(path.name)
    for path in TARGET.glob("*.java"):
        if path.name not in expected:
            path.unlink()
    print(f"generated {len(expected)} Java contracts")


if __name__ == "__main__":
    main()
