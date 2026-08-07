#!/usr/bin/env python3
"""Static guardrails for SQL that otherwise fail only at Spring/PostgreSQL runtime.

The audit deliberately focuses on failure classes that javac and architecture checks
cannot see:
- unsafe concatenation boundaries between SQL fragments,
- statically resolvable NamedParameterJdbcTemplate parameter mismatches,
- table-alias column references that do not exist in the canonical Flyway schema,
- drift between the legacy-v1 compatibility baseline and the current modular schema.

It is intentionally conservative. Dynamic identifier allowlists remain owned by the
module service/repository and must also be exercised by PostgreSQL integration tests.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
JAVA = ROOT / "spring-api" / "src" / "main" / "java"
MIGRATIONS = ROOT / "spring-api" / "src" / "main" / "resources" / "db" / "migration"

SQL_METHODS = ("query", "optional", "required", "update", "count", "insertReturningId")
SQL_KEYWORDS = {
    "where", "and", "or", "order", "group", "join", "left", "right", "inner", "outer",
    "on", "limit", "offset", "returning", "set", "values",
}
SAFE_LEFT_BOUNDARY = set(" (,.=<>+-*/;[]")
SAFE_RIGHT_BOUNDARY = set(" ),.=<>+-*/;[]")


@dataclass(frozen=True)
class Issue:
    path: Path
    line: int
    detail: str

    def render(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}: {self.detail}"


def _decode_java_string(raw: str) -> str:
    replacements = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
    return re.sub(r"\\([nrt\"\\])", lambda match: replacements[match.group(1)], raw)


def _text_block_value(source: str, match: re.Match[str]) -> str:
    raw = match.group("body")
    if raw.startswith("\r\n"):
        raw = raw[2:]
    elif raw.startswith(("\n", "\r")):
        raw = raw[1:]

    closing_start = match.start("close")
    line_start = source.rfind("\n", 0, closing_start) + 1
    closing_indent = len(source[line_start:closing_start])
    lines = raw.splitlines(keepends=True)
    indents = [
        len(line.rstrip("\r\n")) - len(line.rstrip("\r\n").lstrip(" \t"))
        for line in lines
        if line.rstrip("\r\n").strip()
    ]
    indents.append(closing_indent)
    incidental = min(indents) if indents else 0

    value: list[str] = []
    for line in lines:
        body = line.rstrip("\r\n")
        if body.strip():
            body = body[incidental:]
        else:
            body = ""
        value.append(body)
        if line.endswith(("\n", "\r")):
            value.append("\n")
    return "".join(value)


def string_constants() -> dict[str, str]:
    result: dict[str, str] = {}
    text_block = re.compile(
        r"(?:public|private|protected)?\s*static\s+final\s+String\s+(?P<name>\w+)\s*=\s*"
        r"(?P<open>\"\"\")(?P<body>.*?)(?P<close>\"\"\")\s*;",
        re.DOTALL,
    )
    quoted = re.compile(
        r"(?:public|private|protected)?\s*static\s+final\s+String\s+(\w+)\s*=\s*"
        r'"((?:\\.|[^"\\])*)"\s*;'
    )
    for path in JAVA.rglob("*.java"):
        source = path.read_text(encoding="utf-8")
        class_name = path.stem
        for match in text_block.finditer(source):
            result[f"{class_name}.{match.group('name')}"] = _text_block_value(source, match)
        for match in quoted.finditer(source):
            result[f"{class_name}.{match.group(1)}"] = _decode_java_string(match.group(2))
    return result


def parse_schema(paths: Iterable[Path]) -> dict[str, set[str]]:
    schema: dict[str, set[str]] = {}
    create_table = re.compile(
        r"CREATE TABLE(?: IF NOT EXISTS)?\s+([A-Za-z_]\w*)\s*\((.*?)\n\);",
        re.IGNORECASE | re.DOTALL,
    )
    add_column = re.compile(
        r"ALTER TABLE\s+([A-Za-z_]\w*)\s+ADD COLUMN(?: IF NOT EXISTS)?\s+([A-Za-z_]\w*)",
        re.IGNORECASE,
    )
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for match in create_table.finditer(source):
            table = match.group(1).lower()
            columns = schema.setdefault(table, set())
            for raw_line in match.group(2).splitlines():
                line = raw_line.strip()
                if not line or re.match(r"(?i)(primary|foreign|constraint|unique|check)\b", line):
                    continue
                column = re.match(r'"?([A-Za-z_]\w*)"?\s+', line)
                if column:
                    columns.add(column.group(1).lower())
        for match in add_column.finditer(source):
            schema.setdefault(match.group(1).lower(), set()).add(match.group(2).lower())
    return schema


def schema_drift_issues() -> list[Issue]:
    legacy_path = MIGRATIONS / "V1__current_schema_baseline.sql"
    modular_paths = sorted(MIGRATIONS.glob("V[2-9]__*.sql"))
    legacy = parse_schema([legacy_path])
    modular = parse_schema(modular_paths)
    issues: list[Issue] = []
    if set(legacy) != set(modular):
        issues.append(Issue(legacy_path, 1, "Flyway v1 compatibility schema and modular schema expose different tables"))
        return issues
    for table in sorted(legacy):
        if legacy[table] != modular[table]:
            missing = sorted(legacy[table] - modular[table])
            extra = sorted(modular[table] - legacy[table])
            issues.append(Issue(
                legacy_path,
                1,
                f"schema drift for {table}: only-v1={missing} only-modular={extra}",
            ))
    return issues


def _unsafe_boundary(left: str, right: str) -> bool:
    if not left or not right:
        return False
    left_char, right_char = left[-1], right[0]
    if left_char.isspace() or right_char.isspace():
        return False
    if left_char in SAFE_LEFT_BOUNDARY or right_char in SAFE_RIGHT_BOUNDARY:
        return False
    return True


def fragment_boundary_issues(constants: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    constant_ref = r"[A-Z][A-Za-z0-9_]*\.\w+"
    direct_pair = re.compile(rf"({constant_ref})\s*\+\s*({constant_ref})")
    optional_assignment = re.compile(
        rf"String\s+(\w+)\s*=\s*[^;?]+\?\s*({constant_ref}|\"(?:\\.|[^\"\\])*\")\s*:\s*"
        rf"({constant_ref}|\"(?:\\.|[^\"\\])*\")\s*;"
    )
    sandwich = re.compile(rf"({constant_ref})\s*\+\s*(\w+)\s*\+\s*({constant_ref})")
    append = re.compile(rf"\.append\(\s*({constant_ref})\s*\)")

    def resolve(token: str) -> str | None:
        if token.startswith('"'):
            return _decode_java_string(token[1:-1])
        return constants.get(token)

    for path in JAVA.rglob("*.java"):
        if "repository/queries" in path.as_posix():
            continue
        source = path.read_text(encoding="utf-8")
        for match in direct_pair.finditer(source):
            left, right = constants.get(match.group(1)), constants.get(match.group(2))
            if left is not None and right is not None and _unsafe_boundary(left, right):
                issues.append(Issue(path, source.count("\n", 0, match.start()) + 1,
                                    f"SQL fragments can merge tokens: {match.group(1)} + {match.group(2)}"))

        optionals: dict[str, tuple[str, str]] = {}
        for match in optional_assignment.finditer(source):
            first, second = resolve(match.group(2)), resolve(match.group(3))
            if first is not None and second is not None:
                optionals[match.group(1)] = (first, second)
        for match in sandwich.finditer(source):
            left = constants.get(match.group(1))
            right = constants.get(match.group(3))
            variants = optionals.get(match.group(2))
            if left is None or right is None or variants is None:
                continue
            for middle in variants:
                pieces = (left, middle, right) if middle else (left, right)
                if any(_unsafe_boundary(a, b) for a, b in zip(pieces, pieces[1:])):
                    issues.append(Issue(
                        path,
                        source.count("\n", 0, match.start()) + 1,
                        f"optional SQL fragment '{match.group(2)}' can merge adjacent tokens",
                    ))
                    break

        # Appended continuation fragments must provide their own delimiter. This is
        # intentionally strict because conditional StringBuilder branches are hard
        # to reconstruct reliably without compiling/running the method.
        for match in append.finditer(source):
            value = constants.get(match.group(1))
            if value is None or not value:
                continue
            stripped = value.lstrip().lower()
            first_word = stripped.split(None, 1)[0] if stripped else ""
            if first_word in SQL_KEYWORDS and not value[0].isspace():
                issues.append(Issue(
                    path,
                    source.count("\n", 0, match.start()) + 1,
                    f"appended SQL continuation {match.group(1)} has no leading delimiter",
                ))
    return issues


def _scan_call(source: str, opening_paren: int) -> tuple[list[str], int] | tuple[None, None]:
    depth = 1
    index = opening_paren + 1
    argument_start = index
    arguments: list[str] = []
    in_string = False
    in_char = False
    in_text_block = False
    escaped = False
    while index < len(source):
        if in_text_block:
            if source.startswith('"""', index):
                in_text_block = False
                index += 3
                continue
            index += 1
            continue
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if in_char:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_char = False
            index += 1
            continue
        if source.startswith('"""', index):
            in_text_block = True
            index += 3
            continue
        if char == '"':
            in_string = True
        elif char == "'":
            in_char = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                arguments.append(source[argument_start:index].strip())
                return arguments, index
        elif char == "," and depth == 1:
            arguments.append(source[argument_start:index].strip())
            argument_start = index + 1
        index += 1
    return None, None


def _top_level_plus_parts(expression: str) -> list[str] | None:
    parts: list[str] = []
    depth = 0
    in_string = False
    escaped = False
    start = 0
    for index, char in enumerate(expression):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "+" and depth == 0:
            parts.append(expression[start:index].strip())
            start = index + 1
    parts.append(expression[start:].strip())
    return parts


def _evaluate_static_sql(expression: str, constants: dict[str, str]) -> str | None:
    result: list[str] = []
    for part in _top_level_plus_parts(expression):
        token = part.strip().strip("() ")
        if token in constants:
            result.append(constants[token])
        elif re.fullmatch(r'"(?:\\.|[^"\\])*"', token):
            result.append(_decode_java_string(token[1:-1]))
        else:
            return None
    return "".join(result)


def _split_top_level_arguments(body: str) -> list[str]:
    result: list[str] = []
    depth = 0
    in_string = False
    escaped = False
    start = 0
    for index, char in enumerate(body):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            result.append(body[start:index].strip())
            start = index + 1
    result.append(body[start:].strip())
    return result


def _static_parameter_keys(expression: str) -> set[str] | None:
    match = re.match(r"(?:Map\.of|SqlParameters\.ofNullable)\s*\((.*)\)\s*$", expression, re.DOTALL)
    if not match:
        return None
    arguments = _split_top_level_arguments(match.group(1))
    if len(arguments) % 2:
        return None
    keys: set[str] = set()
    for token in arguments[::2]:
        key = re.fullmatch(r'"([^"\\]+)"', token)
        if key is None:
            return None
        keys.add(key.group(1))
    return keys


def static_sql_calls(constants: dict[str, str]) -> Iterable[tuple[Path, int, str, str, list[str]]]:
    methods = "|".join(SQL_METHODS)
    call_start = re.compile(rf"(?:\b[A-Za-z_]\w*\.)?\b({methods})\s*\(")
    for path in JAVA.rglob("*.java"):
        source = path.read_text(encoding="utf-8")
        for match in call_start.finditer(source):
            arguments, _ = _scan_call(source, match.end() - 1)
            if not arguments:
                continue
            sql = _evaluate_static_sql(arguments[0], constants)
            if sql is None or not re.search(r"(?i)\b(select|insert|update|delete|with)\b", sql):
                continue
            yield path, source.count("\n", 0, match.start()) + 1, match.group(1), sql, arguments


def named_parameter_issues(constants: dict[str, str]) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    checked = 0
    for path, line, _method, sql, arguments in static_sql_calls(constants):
        if len(arguments) < 2:
            continue
        keys = _static_parameter_keys(arguments[1])
        if keys is None:
            continue
        checked += 1
        parameters = set(re.findall(r"(?<!:):([A-Za-z][A-Za-z0-9_]*)", sql))
        if parameters != keys:
            issues.append(Issue(
                path,
                line,
                f"Named SQL parameters {sorted(parameters)} do not match supplied keys {sorted(keys)}",
            ))
    return issues, checked


def static_sql_strings() -> Iterable[tuple[Path, int, str, str]]:
    text_block = re.compile(
        r"(?:public|private|protected)?\s*static\s+final\s+String\s+(?P<name>\w+)\s*=\s*"
        r"(?P<open>\"\"\")(?P<body>.*?)(?P<close>\"\"\")\s*;",
        re.DOTALL,
    )
    quoted = re.compile(
        r"(?:public|private|protected)?\s*static\s+final\s+String\s+(\w+)\s*=\s*"
        r'"((?:\\.|[^"\\])*)"\s*;'
    )
    for path in JAVA.rglob("*.java"):
        source = path.read_text(encoding="utf-8")
        for match in text_block.finditer(source):
            yield path, source.count("\n", 0, match.start()) + 1, match.group("name"), _text_block_value(source, match)
        for match in quoted.finditer(source):
            yield path, source.count("\n", 0, match.start()) + 1, match.group(1), _decode_java_string(match.group(2))


def resolved_sql_sources(constants: dict[str, str]) -> Iterable[tuple[Path, int, str, str]]:
    yield from static_sql_strings()
    for path, line, method, sql, _arguments in static_sql_calls(constants):
        yield path, line, f"{method} call", sql


def table_reference_issues(schema: dict[str, set[str]], constants: dict[str, str]) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    checked = 0
    references = (
        re.compile(r"(?i)(?<!:)\b(?:from|join)\s+(?:lateral\s+)?([A-Za-z_]\w*)"),
        re.compile(r"(?im)(?:^|\)\s*)update\s+([A-Za-z_]\w*)"),
        re.compile(r"(?i)\binsert\s+into\s+([A-Za-z_]\w*)"),
        re.compile(r"(?i)\bdelete\s+from\s+([A-Za-z_]\w*)"),
    )
    pseudo_relations = {"excluded", "information_schema", "lateral", "pg_catalog"}
    for path, line, name, sql in resolved_sql_sources(constants):
        ctes = {
            value.lower()
            for value in re.findall(r"(?i)(?:\bwith|,)\s*([A-Za-z_]\w*)\s+as\s*\(", sql)
        }
        for pattern in references:
            for match in pattern.finditer(sql):
                table = match.group(1).lower()
                if table in pseudo_relations or table in ctes:
                    continue
                checked += 1
                if table not in schema:
                    issues.append(Issue(path, line, f"{name} references missing schema table {table}"))
    return issues, checked


def schema_reference_issues(schema: dict[str, set[str]], constants: dict[str, str]) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    checked = 0
    alias_binding = re.compile(
        r"(?i)\b(?:from|join|update)\s+([A-Za-z_]\w*)(?:\s+(?:as\s+)?([A-Za-z_]\w*))?"
    )
    alias_column = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b")
    alias_stop_words = {
        "where", "set", "join", "left", "right", "inner", "outer", "on", "order", "group", "limit", "returning",
    }
    for path, line, name, sql in resolved_sql_sources(constants):
        if not re.search(r"(?i)\b(select|update|insert|delete)\b", sql):
            continue
        bindings: list[tuple[int, str, str]] = []
        for match in alias_binding.finditer(sql):
            table = match.group(1).lower()
            alias = (match.group(2) or table).lower()
            if table in schema and alias not in alias_stop_words:
                bindings.append((match.start(), alias, table))
        for match in alias_column.finditer(sql):
            alias, column = match.group(1).lower(), match.group(2).lower()
            candidates = [binding for binding in bindings if binding[1] == alias]
            if not candidates:
                continue
            checked += 1
            tables = {binding[2] for binding in candidates}
            if column != "*" and all(column not in schema[table] for table in tables):
                closest = min(candidates, key=lambda binding: abs(binding[0] - match.start()))
                table = closest[2]
                issues.append(Issue(
                    path,
                    line,
                    f"{name} references missing schema column {alias}.{column} ({table}.{column})",
                ))
    return issues, checked


def sql_update_schema_issues(schema: dict[str, set[str]]) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    checked = 0
    method = re.compile(
        r"(?ms)^\s*(?:public|protected|private)\s+(?:static\s+)?[\w<>, ?.\[\]]+\s+\w+"
        r"\s*\([^;{}]*?\)\s*\{"
    )
    constructor = re.compile(
        r'SqlUpdate\s+(\w+)\s*=\s*new\s+SqlUpdate\(\s*"([a-z][a-z0-9_]*)"\s*,'
        r'\s*"([a-z][a-z0-9_]*)"'
    )
    for path in JAVA.rglob("*.java"):
        source = path.read_text(encoding="utf-8")
        methods = list(method.finditer(source))
        for index, method_match in enumerate(methods):
            end = methods[index + 1].start() if index + 1 < len(methods) else len(source)
            body = source[method_match.start():end]
            for match in constructor.finditer(body):
                variable, table, id_column = match.groups()
                checked += 1
                if table not in schema:
                    issues.append(Issue(path, source.count("\n", 0, method_match.start() + match.start()) + 1,
                                        f"SqlUpdate targets missing schema table {table}"))
                    continue
                columns = [id_column, *re.findall(
                    rf'\b{re.escape(variable)}\.set\(\s*"([a-z][a-z0-9_]*)"', body
                )]
                for column in columns:
                    if column not in schema[table]:
                        issues.append(Issue(
                            path,
                            source.count("\n", 0, method_match.start() + match.start()) + 1,
                            f"SqlUpdate references missing schema column {table}.{column}",
                        ))
    return issues, checked


def main() -> int:
    constants = string_constants()
    modular_paths = sorted(MIGRATIONS.glob("V[2-9]__*.sql"))
    schema = parse_schema(modular_paths)

    issues: list[Issue] = []
    issues.extend(schema_drift_issues())
    issues.extend(fragment_boundary_issues(constants))
    parameter_issues, checked_calls = named_parameter_issues(constants)
    issues.extend(parameter_issues)
    table_issues, checked_tables = table_reference_issues(schema, constants)
    issues.extend(table_issues)
    schema_issues, checked_columns = schema_reference_issues(schema, constants)
    issues.extend(schema_issues)
    update_issues, checked_updates = sql_update_schema_issues(schema)
    issues.extend(update_issues)

    if issues:
        for issue in issues:
            print(f"[sql-runtime] {issue.render()}", file=sys.stderr)
        print(f"[sql-runtime] FAIL: {len(issues)} issue(s)", file=sys.stderr)
        return 1

    print(
        f"[sql-runtime] OK: {len(schema)} schema tables, {checked_tables} table refs, "
        f"{checked_columns} alias-column refs, {checked_calls} static parameterized calls, "
        f"{checked_updates} SqlUpdate schemas"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
