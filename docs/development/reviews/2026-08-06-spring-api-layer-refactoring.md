# Spring API Refactoring

## Goal

The Spring API was converted from a centrally dispatched, handler-based structure to classic,
domain-modular Spring layers:

```text
OpenAPI contract
  -> generated API interface + API DTO
  -> module controller
  -> module service
  -> module repository
  -> module mapper
  -> API/module DTO or entity / PostgreSQL
```

The `controller`, `filter`, `service`, `mapper`, `dto`, `entity`, and `repository` packages
live inside the corresponding business domain. Ambiguous generic `model` packages are not part
of the target architecture: transport data belongs in `dto`, persistence objects in `entity`,
and catalogs in the responsible service or repository layer. A layer is created only when the
module has a real responsibility for it; empty placeholders or artificial abstractions are not added.

## Cleaned starting state

Before the refactoring, HTTP routes were wired through a central dispatcher and module-specific
operation handlers. Business modules were partly organized flatly, services accessed a generic
JDBC service, and SQL was distributed across 43 service classes. Transport, business logic, and
persistence were therefore insufficiently separated.

## Implemented changes

- 177 OpenAPI operations are described by 34 generated typed API interfaces and implemented
  uniquely by 26 module controllers.
- 179 generated request/response DTOs represent the HTTP contract; named module DTOs encapsulate
  internal persistence and integration transfers.
- Controllers and public service boundaries transport neither entities nor JDBC rows or raw maps.
  Only mappers create API representations.
- The central API dispatcher, operation-handler base classes, 26 concrete operation handlers, and
  old generated controllers were removed.
- Controllers contain only HTTP binding and delegate to services.
- Business logic, authorization, and transaction boundaries live in module services.
- Generic JDBC access is reachable only from persistence and repository classes.
- SQL definitions were moved from 43 services into domain-specific query catalogs under
  `repository/queries`. Services contain no SQL literals.
- Mappers, DTOs, entities, filters, and repositories were assigned to their respective business
  modules and unambiguous layer packages.
- Core health/readiness paths also follow Controller -> Service -> Repository.
- Architecture and generation gates were adapted to the new layer model and prevent regressions
  to dispatcher, handler, or service-to-JDBC structures.
- Affected tests and documentation were updated for the new packages and repository dependencies.

## Enforced architecture rules

`infrastructure/scripts/quality/audit_spring_backend.py` checks, among other things:

- complete and unique implementation of all contract operations;
- no central dispatchers or operation handlers;
- no route mappings outside generated API interfaces;
- no controller access to repository, entity, JDBC, Flyway, or SQL;
- no service access to generic JDBC and no SQL literals in services;
- no repository dependencies on upper layers;
- explicit layer packages for executable business-module classes;
- existing batch, security, and size invariants.

## Local validation

Successfully executed:

- contract generation: 34 interfaces and 177 operations consistent;
- Spring architecture audit: 26 controllers and 466 production Java sources consistent;
- internal package/import consistency gate;
- security audit;
- agent/module cache gate;
- structural Java 21 compilation of the original layer refactoring against isolated
  Spring/JPA interface stubs;
- structural compilation of all 21 test sources against the same stubs.

## Environment limit

Maven was not installed in the provided execution environment and external network/DNS access
was unavailable. Therefore `mvn -f spring-api/pom.xml verify`, real Spring context starts, and
PostgreSQL Testcontainers could not be run here. Stub compilation checks Java types, signatures,
packages, and internal dependencies, but does not replace a final Maven/runtime test in normal
CI or a development environment.

## DTO transition

The subsequent DTO refactoring is documented completely in the
[DTO refactoring report](2026-08-06-spring-api-dto-refactoring.md). The current target architecture
enforces typed HTTP DTOs, module-specific transfer DTOs, and mappers as the only representation boundary.

## Subsequent repository cleanup

The following structural cleanup removed the remaining generic `model` packages. Internal build and
security transfer objects now live in module `dto` packages, seed and event catalogs in the responsible
repository/service layer. An unused Spring Data repository, dead controller helpers, and the map-based
`RequestParameters` intermediate step were also removed. The architecture gate prevents empty source
directories, generic `model` packages, raw parameter maps in controllers, and repository types without
application consumers.
