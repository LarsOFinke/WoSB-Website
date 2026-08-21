#!/usr/bin/env python3
"""Fail when any Spring production class or module falls outside the go-live test strategy."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAIN = ROOT / "spring-api/src/main/java/eu/royalblackwater/api"
TEST = ROOT / "spring-api/src/test/java/eu/royalblackwater/api"
POM = ROOT / "spring-api/pom.xml"
VALIDATE = ROOT / "infrastructure/scripts/quality/validate.sh"
CHECK_REPOSITORY = ROOT / "infrastructure/scripts/quality/check_repository.py"
APPLICATION_YML = ROOT / "spring-api/src/main/resources/application.yml"
BUSINESS_SUFFIXES = (
    "Service.java", "Policy.java", "Calculator.java", "Validator.java",
    "Initializer.java", "Seeder.java", "Worker.java",
)
GLOBAL_STRATEGY = (
    TEST / "testing/BackendServiceSurfaceTest.java",
    TEST / "testing/BackendComponentSurfaceTest.java",
    TEST / "testing/ModuleDtoContractTest.java",
    TEST / "testing/PersistenceEntityContractTest.java",
    TEST / "integration/ApiSurfaceIntegrationTest.java",
    TEST / "integration/ApplicationIntegrationTest.java",
    TEST / "integration/FlywayMigrationCompatibilityTest.java",
    TEST / "dto/GeneratedDtoContractTest.java",
    TEST / "persistence/PersistenceUtilitiesTest.java",
)
FOCUSED_GO_LIVE_TESTS = (
    TEST / "account/entity/AccountEntityBehaviorTest.java",
    TEST / "builds/BuildPayloadTest.java",
    TEST / "builds/BuildShipSnapshotTest.java",
    TEST / "config/ApiExceptionHandlerTest.java",
    TEST / "persistence/JdbcQueryServiceTest.java",
    TEST / "security/CsrfCookieFilterTest.java",
    TEST / "security/SessionAuthenticationFilterTest.java",
    TEST / "shared/web/ApiControllerSupportTest.java",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[backend-tests] {message}")


def module_names(root: Path) -> set[str]:
    return {path.name for path in root.iterdir() if path.is_dir() and any(path.rglob("*.java"))}


def business_component_sources() -> set[Path]:
    return {
        path for path in MAIN.rglob("*.java")
        if path.name.endswith(BUSINESS_SUFFIXES) and path.parent != MAIN / "dto"
    }


def source_declares_behavior(path: Path, *, entity: bool = False) -> bool:
    text = path.read_text(encoding="utf-8")
    class_name = path.stem
    if re.search(rf"(?m)^\s*public\s+{re.escape(class_name)}\s*\{{", text):
        return True
    method_pattern = re.compile(
        r"(?m)^\s*(?:public|protected|private)\s+(?:static\s+)?"
        r"(?:[\w<>?,.\[\] ]+\s+)?(\w+)\s*\([^;{}]*\)\s*\{")
    for match in method_pattern.finditer(text):
        name = match.group(1)
        if name == class_name:
            continue
        if entity and (name.startswith("get") or name.startswith("set") or name.startswith("is")):
            continue
        return True
    return False


def tests_mentioning(class_name: str, *, module: str | None = None) -> list[Path]:
    result: list[Path] = []
    for path in TEST.rglob("*Test.java"):
        relative = path.relative_to(TEST)
        if module is not None and relative.parts[0] != module:
            continue
        if re.search(rf"\b{re.escape(class_name)}\b", path.read_text(encoding="utf-8")):
            result.append(path)
    return sorted(result)


def classify_sources() -> dict[str, set[Path]]:
    all_sources = set(MAIN.rglob("*.java"))
    generated_dtos = set((MAIN / "dto").glob("*.java"))
    sql_catalogs = {path for path in all_sources if "repository" in path.parts and "queries" in path.parts}
    business = business_component_sources()
    controllers = {path for path in all_sources if path.parent.name == "controller"}
    mappers = {path for path in all_sources if path.parent.name == "mapper"}
    repositories = {path for path in all_sources if path.parent.name == "repository" and path not in sql_catalogs}
    entities = {path for path in all_sources if path.parent.name == "entity"}
    module_dtos = {path for path in all_sources if path.parent.name == "dto" and path not in generated_dtos}
    filters = {path for path in all_sources if path.parent.name == "filter"}
    configs = {path for path in all_sources if path.relative_to(MAIN).parts[0] == "config"}
    service_helpers = {path for path in all_sources if path.parent.name == "service" and path not in business}
    application = {MAIN / "RbfApiApplication.java"}
    persistence_helpers = {
        path for path in all_sources
        if path.relative_to(MAIN).parts[0] == "persistence" and path not in business
    }
    shared_web_helpers = {
        path for path in all_sources
        if path.relative_to(MAIN).parts[:2] == ("shared", "web")
    }
    core_utilities = {
        path for path in all_sources
        if path.relative_to(MAIN).parts[:2] == ("core", "util")
    }

    groups = {
        "generated DTO": generated_dtos,
        "SQL catalog": sql_catalogs,
        "business component": business,
        "controller": controllers,
        "mapper": mappers,
        "repository": repositories,
        "entity": entities,
        "module DTO": module_dtos,
        "filter": filters,
        "configuration": configs,
        "service helper": service_helpers,
        "application": application,
        "persistence helper": persistence_helpers,
        "shared web helper": shared_web_helpers,
        "core utility": core_utilities,
    }

    owners: dict[Path, list[str]] = defaultdict(list)
    for group, paths in groups.items():
        for path in paths:
            owners[path].append(group)
    overlaps = {path: names for path, names in owners.items() if len(names) > 1}
    require(not overlaps, "production source belongs to multiple test strategies: " + "; ".join(
        f"{path.relative_to(ROOT)} -> {','.join(names)}" for path, names in sorted(overlaps.items())))
    unclassified = sorted(all_sources - set(owners))
    require(not unclassified, "production source has no explicit test strategy: " + ", ".join(
        str(path.relative_to(ROOT)) for path in unclassified))
    return groups


def main() -> None:
    require(MAIN.is_dir() and TEST.is_dir(), "Spring source/test roots are missing")
    production_modules = module_names(MAIN)
    test_modules = {module for module in production_modules if (TEST / module).is_dir()
                    and any((TEST / module).rglob("*Test.java"))}
    missing_modules = sorted(production_modules - test_modules)
    require(not missing_modules,
            "production modules without a module-local test: " + ", ".join(missing_modules))

    for path in (*GLOBAL_STRATEGY, *FOCUSED_GO_LIVE_TESTS):
        require(path.is_file(), f"missing backend test strategy: {path.relative_to(ROOT)}")

    groups = classify_sources()
    business_components = groups["business component"]
    require(business_components, "no business components discovered")
    require(MAIN / "persistence/JdbcQueryService.java" in business_components,
            "business surface discovery must include persistence/JdbcQueryService.java")

    # Generic execution is mandatory, but it is not accepted as the only test for business behavior.
    surface = (TEST / "testing/BackendServiceSurfaceTest.java").read_text(encoding="utf-8")
    for suffix in BUSINESS_SUFFIXES:
        require(f'"{suffix}"' in surface,
                f"business surface discovery no longer includes {suffix}")
    require('SERVICE_ROOT.resolve("dto")' in surface,
            "business surface must exclude only generator-owned root DTO records, not nested packages")
    missing_focused: list[str] = []
    for source in sorted(business_components):
        module = source.relative_to(MAIN).parts[0]
        if not tests_mentioning(source.stem, module=module):
            missing_focused.append(str(source.relative_to(ROOT)))
    require(not missing_focused,
            "business components without a module-local focused semantic test: " + ", ".join(missing_focused))

    service_helpers = groups["service helper"]
    for source in sorted(service_helpers):
        require(tests_mentioning(source.stem),
                f"service helper lacks an explicit test reference: {source.relative_to(ROOT)}")

    for source in sorted(groups["core utility"]):
        require(tests_mentioning(source.stem, module="core"),
                f"core utility lacks an explicit test reference: {source.relative_to(ROOT)}")

    component_surface = (TEST / "testing/BackendComponentSurfaceTest.java").read_text(encoding="utf-8")
    for token in ('"controller"', '"mapper"', '"repository"', '"config"', '"persistence"', '"shared"'):
        require(token in component_surface,
                f"non-business component surface no longer inventories {token}")

    controllers = groups["controller"]
    repositories = groups["repository"]
    mappers = groups["mapper"]
    entities = groups["entity"]
    sql_catalogs = groups["SQL catalog"]
    generated_dtos = groups["generated DTO"]
    module_dtos = groups["module DTO"]
    filters = groups["filter"]
    configs = groups["configuration"]
    require(controllers and repositories and mappers and entities and sql_catalogs and generated_dtos
            and module_dtos and filters and configs, "one or more critical backend layers are empty")

    logic_dtos = [path for path in module_dtos if source_declares_behavior(path)]
    logic_entities = [path for path in entities if source_declares_behavior(path, entity=True)]
    for source in (*logic_dtos, *logic_entities):
        require(tests_mentioning(source.stem, module=source.relative_to(MAIN).parts[0]),
                f"logic-bearing type lacks a module-local semantic test reference: {source.relative_to(ROOT)}")
    for source in filters:
        require(any(TEST.rglob(f"{source.stem}Test.java")),
                f"filter lacks a dedicated test: {source.relative_to(ROOT)}")

    api_surface = (TEST / "integration/ApiSurfaceIntegrationTest.java").read_text(encoding="utf-8")
    require("everyContractOperationEnforcesItsAnonymousSecurityBoundary" in api_surface,
            "API surface no longer verifies anonymous authorization boundaries")
    require("everyAuthenticatedWriteRequiresCsrf" in api_surface,
            "API surface no longer verifies CSRF on authenticated writes")
    require("contractOperationInventoryRemainsFullyRepresented" in api_surface,
            "API surface no longer pins the complete OpenAPI operation inventory")

    application_integration = (TEST / "integration/ApplicationIntegrationTest.java").read_text(encoding="utf-8")
    require("RbfApiApplication" in application_integration or "SpringBootTest" in application_integration,
            "application bootstrap is not covered by the integration suite")

    validate = VALIDATE.read_text(encoding="utf-8")
    repository_gate = CHECK_REPOSITORY.read_text(encoding="utf-8")
    require("check_backend_test_coverage.py" in validate,
            "full validation must execute the backend-completeness audit")
    require("audit_sql_runtime.py" in repository_gate,
            "repository validation must execute the SQL-runtime audit")
    application = APPLICATION_YML.read_text(encoding="utf-8")
    require("ddl-auto: validate" in application,
            "JPA entity/schema compatibility must remain fail-closed with Hibernate validation")

    pom = POM.read_text(encoding="utf-8")
    require("jacoco-maven-plugin" in pom and "coverage-check" in pom,
            "JaCoCo verify gate is missing")
    require("<element>PACKAGE</element>" in pom and "<counter>CLASS</counter>" in pom
            and "<value>MISSEDCOUNT</value>" in pom,
            "JaCoCo package gate must reject completely missed production classes")
    line_match = re.search(r"<coverage\.line\.minimum>([0-9.]+)</coverage\.line\.minimum>", pom)
    branch_match = re.search(r"<coverage\.branch\.minimum>([0-9.]+)</coverage\.branch\.minimum>", pom)
    method_match = re.search(r"<coverage\.method\.minimum>([0-9.]+)</coverage\.method\.minimum>", pom)
    package_match = re.search(r"<coverage\.package\.line\.minimum>([0-9.]+)</coverage\.package\.line\.minimum>", pom)
    require(line_match is not None and float(line_match.group(1)) >= 0.80,
            "Go-live line coverage floor must be at least 80%")
    require(branch_match is not None and float(branch_match.group(1)) >= 0.65,
            "Go-live branch coverage floor must be at least 65%")
    require(method_match is not None and float(method_match.group(1)) >= 0.80,
            "Go-live method coverage floor must be at least 80%")
    require(package_match is not None and float(package_match.group(1)) >= 0.60,
            "Go-live per-package line coverage floor must be at least 60%")
    require("@{argLine}" in pom and "jacoco-maven-plugin" in pom,
            "Surefire must preserve the JaCoCo prepare-agent argLine")

    require("<exclude>eu/royalblackwater/api/dto/**</exclude>" in pom,
            "only generator-owned root OpenAPI DTOs may use the DTO JaCoCo exclusion")
    require("<exclude>**/repository/queries/**</exclude>" in pom,
            "static SQL catalogs must retain their dedicated SQL-audit exclusion")
    for forbidden in ("<exclude>**/dto/**</exclude>", "<exclude>**/entity/**</exclude>",
                      "<exclude>**/*Application*</exclude>"):
        require(forbidden not in pom,
                f"over-broad JaCoCo exclusion would hide executable production logic: {forbidden}")

    all_sources = set(MAIN.rglob("*.java"))
    print(
        f"[backend-tests] OK: {len(all_sources)}/{len(all_sources)} production classes classified, "
        f"{len(production_modules)}/{len(production_modules)} modules, "
        f"{len(business_components)} focused business components + {len(service_helpers)} service helpers, "
        f"{len(controllers)} controllers, {len(repositories)} repositories, {len(mappers)} mappers, "
        f"{len(entities)} entities, {len(sql_catalogs)} SQL catalogs, {len(generated_dtos)} generated DTOs, "
        f"{len(module_dtos)} module DTOs ({len(logic_dtos)} behavior-bearing), {len(filters)} filters, "
        f"{len(configs)} configuration classes"
    )


if __name__ == "__main__":
    main()
