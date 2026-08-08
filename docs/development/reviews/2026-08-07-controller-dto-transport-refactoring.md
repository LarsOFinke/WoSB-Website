# Controller/DTO Transport Refactoring

Date: 2026-08-07

## Reason

After the complete Spring migration, two historical transport structures still existed in parallel
with the actual module architecture:

- the root `contracts/` directory, which mixed OpenAPI, reference data, test fixtures, and a backup
  protocol without a shared functional owner;
- generated Java `*Api` interfaces under `api/contract/api`, which formed a second runtime transport
  layer between OpenAPI and module controllers.

The application already uses immutable API DTOs and modular controllers, services, mappers, and
repositories. The additional interface layer had no independent functional responsibility and made
navigation and ownership harder.

## Decision

The external HTTP specification remains, but it is **not a backend layer**. It now lives as
`openapi/openapi.json` outside the Java runtime structure and is the canonical source for HTTP schema,
operations, and API DTO generation.

Only API DTOs under `spring-api/src/main/java/eu/royalblackwater/api/dto/` are generated. The 26 module
controllers own their Spring MVC mappings and Bean Validation bindings directly. A static audit compares
all 177 controller operations with OpenAPI and prevents drift.

The runtime dependency is therefore:

```text
HTTP
  -> Filter / Security
  -> Controller (routing + binding + @Valid API DTO)
  -> Service (business logic, policy, transaction)
  -> Repository (persistence)

Mapper <-> API/module DTO / entity / DB row
```

Entities remain persistence types. API DTOs remain transport types. Services do not construct API
representations; that responsibility belongs to explicit mappers.

## Removed legacy structures

- `spring-api/.../api/contract/api/*Api.java`
- `generate_spring_routes.py`
- `ContractConversionService`
- root catch-all directory `contracts/`
- unreferenced `database-metadata.json`

Content still required was assigned to its owner:

- OpenAPI: `openapi/openapi.json`
- build/webhook reference data: `spring-api/src/main/reference/`
- build-calculation fixtures: `frontend/tests/fixtures/`
- backup protocol: `infrastructure/scripts/backup/`

## Mapper cleanup

The generic `ContractConversionService` was removed. Build, ship, master-data, and webhook conversions
are explicit typed mappers again. Dynamic Jackson conversion is permitted only inside a concrete mapper
when the source itself intentionally contains dynamic integration JSON (for example backup control status).

## New gates

`audit_controller_contract.py` checks OpenAPI against the actual controller bindings. In addition,
`audit_spring_backend.py` prevents reintroducing a Java `contract` layer or generic contract-conversion service.

For future API changes:

1. change `openapi/openapi.json`;
2. generate API DTOs;
3. adapt the responsible module controller directly;
4. run the controller/OpenAPI audit;
5. change service, mapper, repository, and tests only according to their responsibilities.

This keeps the OpenAPI specification as a stable external contract without mistaking it for a parallel
runtime architecture.
