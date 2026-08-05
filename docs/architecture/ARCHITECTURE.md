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
  ├─ Spring Security / CSRF / session authentication
  ├─ operation dispatcher and domain services
  ├─ JDBC/JPA repositories and MapStruct mappers
  ├─ Flyway migrations and versioned reference-data seed
  ├─ uploads and host-control inbox
  └─ PostgreSQL
```

The gateway is the only public container. PostgreSQL binds to loopback for administration and otherwise lives on an internal network. The API has a separate outbound network only for explicitly allow-listed integrations.

## Backend boundaries

`contracts/api-contract.json` is the versioned HTTP contract. Generated Spring controllers bind and validate requests, then delegate by `operationId` to exactly one handler. Startup fails on missing or duplicate handlers.

Domain services own authorization, transactions and audit semantics. Repositories use parameterized SQL or bounded JPA fetch plans. Hibernate Open Session in View is disabled, so response assembly cannot issue accidental lazy queries.

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
