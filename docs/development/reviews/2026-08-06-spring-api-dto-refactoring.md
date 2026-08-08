# Spring API DTO Refactoring

## Target architecture

The Spring API now has an explicit translation boundary between HTTP contract, business
logic, and persistence that is enforced by gates:

```text
OpenAPI contract
  -> generated API interface
  -> generated request/response DTO
  -> module controller
  -> module service
  -> module repository
  -> module mapper
  -> API DTO / module DTO / entity / database row
```

Controllers and public service methods transport no entities, JDBC rows, or freely passed
`Map<String, Object>` structures. Mappers are the only layer that creates API representations
or translates between repository/entity data and DTOs.

## Implemented changes

- The OpenAPI contract generates **179 immutable Java records** under
  `eu.royalblackwater.api.dto`.
- All **34 generated API interfaces** have concrete `ResponseEntity<T>`,
  `ResponseEntity<List<T>>`, `ResponseEntity<Resource>`, or `ResponseEntity<Void>`
  signatures; wildcards were removed.
- All **177 API operations** remain uniquely wired through **26 controllers**.
- Each of the 20 HTTP business modules has a mapper layer.
- Request bodies remain typed from the generated interface to the service; controllers no
  longer degrade DTOs to `Object` and cast them again.
- Controllers no longer create API representations themselves.
- Services no longer instantiate generated API DTOs themselves; they delegate representation
  construction to module mappers.
- Public service signatures expose neither entities nor database/JSON rows as raw maps.
- Binary downloads are transported through `BinaryDownloadDto` instead of untyped responses.
- Persisted file metadata, fleet target memberships, and Raid Helper integration data have
  named module DTOs.
- The intentionally dynamic Raid Helper JSON payload is encapsulated in
  `RaidHelperJsonPayloadDto`; free JSON structures are not treated as database rows.
- Master-data rows, backup/update control files, security aggregates, build statistics,
  legal environment fallbacks, and webhook, privacy, fleet, and account representations are
  built through domain-specific mappers.

## DTO categories

### Generated API DTOs

`spring-api/src/main/java/eu/royalblackwater/api/dto/`

These records represent only the versioned HTTP contract and are generated with
`generate_java_contracts.py` from `contracts/api-contract.json`. They are not edited manually.

### Module-internal DTOs

Named transfer objects live in the relevant `<domain>/dto` package. Current examples include:

- `files/dto/StoredFileDto`
- `fleet/dto/FleetMembershipTargetDto`
- `raidhelper/dto/RaidHelperConnectionDto`
- `raidhelper/dto/RaidHelperDestinationConfigDto`
- `raidhelper/dto/RaidHelperTemplateConfigDto`
- `raidhelper/dto/RaidHelperEventDto`
- `raidhelper/dto/RaidHelperDeliveryDto`
- `raidhelper/dto/RaidHelperJsonPayloadDto`
- `shared/dto/BinaryDownloadDto`

These DTOs encapsulate business- or integration-related transfers that are not part of the
public HTTP contract.

## Enforced architecture rules

`audit_spring_backend.py` and `check_repository.py` now prevent:

- `ResponseEntity<?>` in generated interfaces or controllers;
- entity, repository, JDBC, or SQL access from controllers;
- degrading typed request DTOs to `Object`;
- API DTO construction in controllers or services;
- entities or raw maps at public service boundaries;
- DTO dependencies on controllers, services, repositories, or entities;
- HTTP modules without a mapper layer;
- stale, missing, or incorrectly placed generated API DTOs;
- legacy transport models in the former contract package.

The DTO generator now has a fail-closed `--check` mode. The repository gate compares all
generated sources byte-for-byte with the current OpenAPI contract.

## Validation

Successfully executed:

- Spring architecture audit: 177 operations, 34 API interfaces, 26 controllers, and
  466 production Java sources;
- DTO generator check: 179 current API DTOs;
- Java 21 syntax check: 487 production and test sources;
- repository, documentation, security, CSS, and strict-tree gates;
- infrastructure and update/artifact tests;
- recovery tests: 8 passed;
- dependency-free frontend tests: 157 passed.

## Environment limit

Maven 3.9 is not installed in the provided execution environment and external dependency
downloads are unavailable. Therefore `mvn -f spring-api/pom.xml verify`, a real Spring
context start, and PostgreSQL Testcontainers could not be run again here. Existing Java
syntax, architecture, generator, repository, and integration gates are green; the normal
Maven/runtime run remains a CI task or a task for a development environment with the Maven
toolchain.

## Subsequent repository cleanup

The following structural cleanup removed the remaining generic `model` packages. Internal
build and security transfer objects now live in module `dto` packages, while seed and event
catalogs live in the responsible repository/service layer. It also removed an unused Spring
Data repository, dead controller helpers, and the map-based `RequestParameters` intermediate
step. The architecture gate prevents empty source directories, generic `model` packages, raw
parameter maps in controllers, and repository types without application consumers.
