# System architecture

Die Verantwortungen und Diagnoseeinstiege jedes Backend-, Frontend- und
Infrastrukturmoduls sind im [Modulkatalog](MODULE_CATALOG.md) zusammengeführt.

## Runtime

```text
Browser
  ↓ HTTPS
NGINX gateway
  ↓ private Docker network
Spring Boot API
  ├─ Spring Security / CSRF / request filters
  ├─ controller-owned Spring MVC bindings + generated API DTOs
  ├─ module-owned controllers + domain services
  ├─ explicit mappers + module-owned JDBC/JPA repositories
  ├─ Flyway migrations and versioned reference-data seed
  ├─ uploads and host-control inbox
  └─ PostgreSQL
```

The gateway is the only public container. PostgreSQL binds to loopback for administration and otherwise lives on an internal network. The API has a separate outbound network only for explicitly allow-listed integrations.

## Backend boundaries

`openapi/openapi.json` is the versioned external HTTP specification. The DTO
generator creates immutable transport records under `api/dto`; it does not create
a runtime contract layer. Module-owned `@RestController` classes own their Spring
MVC mappings and bind/validate generated request DTOs directly.
`audit_controller_contract.py` compares all 177 controller routes, parameters,
request bodies, multipart media types and success response types against OpenAPI.
The structural audit rejects missing/duplicate mappings and controller bypasses of
the service layer.

Domain services own authorization, transactions and audit semantics. Every domain is
split into explicit `controller`, `filter`, `service`, `mapper`, `dto`, `entity` and
`repository` packages as applicable. Generic `model` packages are intentionally
forbidden: transition/value objects belong to the module `dto` package, persistence
state to `entity`, and catalogs to their owning service or repository. Services depend on module repositories rather
than the generic JDBC executor. Repository implementations own database access, and
module-local `repository/queries` catalogs own SQL definitions; SQL literals are
prohibited in services.

The runtime dependency direction is explicit: filters/security execute before the
module controller; the controller owns HTTP binding and DTO validation and delegates
to a service; the service orchestrates authorization, transactions, repositories
and mappers; repositories own persistence. Mappers do not own business
rules or database access.

The transport boundary is DTO-only: controllers and public service methods do not
expose entities, JDBC rows or raw JSON/database maps. Module mappers translate
repository rows and entities into generated API DTOs or named internal DTOs. Dynamic
third-party JSON is wrapped in an integration-specific DTO before it crosses a
service boundary. Hibernate Open Session in View is disabled, so response assembly
cannot issue accidental lazy queries.

Java imports are treated as part of this boundary: duplicate, trivially unused and
unresolved project-internal imports fail the offline Spring audit. Full type
compatibility—including MapStruct generated code—remains a compiler concern and is
therefore validated by Maven in the release gate.

## Persistence

Flyway is the only schema owner. Hibernate runs with `ddl-auto=validate`. Existing
installations retain the immutable `V1__current_schema_baseline.sql` history. New
empty databases select the B2 modular baseline marker and apply the focused
V3–V7 schema migrations; later changes continue as small forward migrations.
Existing installations from the retired schema manager pass a one-time
fingerprint and adoption gate before normal Flyway validation.

Reference data is embedded below `spring-api/src/main/resources/seed` and applied idempotently by Spring. Administrative overrides are preserved explicitly.

## Security

Spring Security is the sole security boundary. Cookie sessions are stored as hashes, mutating requests require CSRF, host and origin boundaries are checked, CORS is allow-list based, and `/api/admin/**` requires the administrator authority. Secrets use a mandatory rotating Fernet-compatible key ring.

## Query discipline

Growing lists use bounded `search`, `limit`, `offset` and domain-specific filters. Related collections are loaded with grouped queries, projections or explicit batch reads. The static Spring audit rejects known N+1 and multi-bag patterns; integration tests cover critical query counts.

## Operations

The API never runs privileged host commands. It writes owner-only JSON requests to an unprivileged inbox. Root-owned systemd runners claim requests through no-follow descriptors and publish world-readable status files without exposing secrets.

Origin deployments use a dedicated key-authenticated SSH administrator rather
than an application or personal account. `deploy.sh --configure` can provision
that account through a one-time VPS bootstrap identity, verifies key-only access
and passwordless non-interactive sudo, then continues the artifact deployment in
the same run. Persistent releases, configuration, database and recovery state
live below `/srv/rbf`; `/tmp/rbf-release` is transfer staging only.

## Quality boundaries

The architecture is considered healthy when domain ownership remains explicit,
queries and payloads are bounded, security/privacy controls are server enforced,
and application, schema and persistent data can be deployed or restored as one
coherent version. Executable Java and frontend JavaScript modules are capped at
420 lines; declarative locale catalogs are the narrow documented exception.
Spring HTTP behavior is exercised against PostgreSQL Testcontainers, while
Playwright covers critical browser navigation, accessibility and form contracts.
The measurable repository-wide requirements and definition of done are maintained
in `docs/development/QUALITY_STANDARDS.md`.
