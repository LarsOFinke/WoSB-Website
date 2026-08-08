# Spring API Type and Import Review, August 7, 2026

## Reason

After the layer, DTO, and repository cleanup, IDE/compiler errors were reported for missing
imports and incompatible conversions. The previous Java check was intentionally only a parser
check and could not detect such symbol and generic-type errors without complete Maven dependencies.

## Errors found and fixed

- `RegistrationService` used `AccountDtoMapper` without importing the mapper.
- `UserAdministrationService` used `AccountDtoMapper` without importing the mapper.
- `PersonalDataExportService` declared export categories as `Map<String,Object>`, although
  `PrivacyDtoMapper` and the generated `PersonalDataExportRead` expect a
  `Map<String,List<Map<String,Object>>>`. The service variable is now typed exactly to the DTO contract.
- `RaidHelperProbeService` still called the removed helper method `result(...)` after the mapper
  refactoring. The success case now uses `RaidHelperDtoMapper.profileTestResult(...)` like all
  other probe results.
- The last demonstrably unused import (`HttpStatus.FORBIDDEN` in `CalendarService`) was removed.

## Binding target architecture

```text
OpenAPI contract
  -> generated API DTOs + generated *Api interfaces
  -> module controller
  -> service
  -> repository -> PostgreSQL
       |
       +-> mapper -> API/module DTO
```

Filters and Spring Security execute before the controller. Controllers own HTTP binding and delegate
business work. Services own business logic, authorization, and transactions. Repositories own
persistence and SQL. Mappers are the only representation boundary between API/module DTOs, entities,
and repository rows. Generic `model` packages and operation handlers are no longer part of the architecture.

## New regression protection

`infrastructure/scripts/quality/audit_spring_backend.py` additionally checks all Java sources in
`src/main` and `src/test` for:

- wildcard imports;
- duplicate imports;
- clearly unused imports;
- imports of nonexistent project-internal types;
- common missing project-internal imports for static type references.

This offline check complements Maven but does not replace it. Generic conversions, constructor/record
signatures, MapStruct-generated code, and framework APIs are authoritatively checked by `mvn verify`.

## Verification

Production sources were fully symbolically type-checked with Java 21 and local framework signature stubs.
Result: 465 production sources, no compiler errors. The 21 test sources were also compiled without type
errors against the same symbolically checked production state. An AST-based import check over production
and test sources reported no unused imports. The remaining 13 static `RowValues.*` wildcard imports were
reduced to exactly the conversion functions actually used; a completely unused wildcard import in
`IpBlockService` disappeared entirely. The Spring architecture audit is green and now forbids wildcard imports.

Missing `serialVersionUID` declarations were also added to the three custom serializable exception types.
The extended `-Xlint` run now reports only the known constructor warning in project code in `UserEntity`,
where the bidirectional JPA profile relationship references `this` while constructing the aggregate; this is
not an incompatible conversion or import error.

Regular Maven/MapStruct/Spring compilation remains required in an environment with Maven 3.9+ and resolvable
dependencies; the provided execution environment still contains no Maven toolchain and no external dependency access.
