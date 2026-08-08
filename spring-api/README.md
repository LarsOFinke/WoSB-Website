# Spring Boot API

The Spring application is the portal's complete backend. It natively implements every operation in the specification maintained under `openapi/source/` and assembled into `openapi/openapi.json`, and owns authentication, authorization, domain logic, persistence, Flyway, seeding, audit, integrations, and operational APIs.

Usage, the cookie/CSRF security boundary, error semantics, and the generated endpoint index are documented under `docs/reference/API.md`.

## Module Architecture

`openapi/source/` is the authoring source for the external HTTP specification; `openapi/openapi.json` is the deterministically assembled artifact. Only the transport DTOs under `api/dto/` are generated from it. Spring MVC bindings intentionally live directly in the module controllers: `@GetMapping`/`@PostMapping`, `@PathVariable`, `@RequestParam`, and `@Valid @RequestBody` are controller responsibilities and are checked against OpenAPI by `audit_controller_contract.py`.

Each domain module organizes its code as needed into `controller`, `filter`, `service`, `mapper`, `dto`, `entity`, and `repository`. Generic `model` or `contract` packages are forbidden. Module-internal DTOs encapsulate typed handoffs for domain workflows; API DTOs represent only the HTTP boundary.

Controllers are HTTP-oriented, validate typed request DTOs, and delegate domain work to services. Public service boundaries do not expose entities, JDBC rows, or `Map<String,Object>`. Mappers own entity/row/DTO conversion; generic ObjectMapper-based “contract conversion” is not an application layer. Repositories encapsulate persistence; SQL definitions live within the respective repository layer under `repository/queries`. Services contain neither SQL literals nor access to the generic JDBC executor.

The runtime path is therefore intentionally unambiguous:

```text
HTTP -> Filter/Security -> Controller -> Service -> Repository -> PostgreSQL
                           |           |
                           |           +-> Mapper <-> API/module DTO/entity/row
                           +-> DTO validation + HTTP status/headers/cookies
```

Import and type consistency are additionally checked by the Spring structural audit;
`mvn verify` remains the authoritative check for complete Java/MapStruct compilation and Spring integration.

```bash
mvn -f spring-api/pom.xml verify
mvn -f spring-api/pom.xml spring-boot:run
```

Important rules:

- Java 21 and Spring Boot 4.1.
- PostgreSQL as the production database.
- Flyway is the sole schema owner.
- Hibernate validates only; Open Session in View is disabled.
- MapStruct fails on unmapped target fields.
- Spring Security and CSRF protect all private operations.
- List queries must be batched and pagination-ready.
