# System architecture

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

Flyway is the only schema owner. Hibernate runs with `ddl-auto=validate`. New installations apply `V1__current_schema_baseline.sql` and later forward migrations. Existing installations from the retired schema manager pass a one-time fingerprint and adoption gate before normal Flyway validation.

Reference data is embedded below `spring-api/src/main/resources/seed` and applied idempotently by Spring. Administrative overrides are preserved explicitly.

## Security

Spring Security is the sole security boundary. Cookie sessions are stored as hashes, mutating requests require CSRF, host and origin boundaries are checked, CORS is allow-list based, and `/api/admin/**` requires the administrator authority. Secrets use a mandatory rotating Fernet-compatible key ring.

## Query discipline

Growing lists use bounded `search`, `limit`, `offset` and domain-specific filters. Related collections are loaded with grouped queries, projections or explicit batch reads. The static Spring audit rejects known N+1 and multi-bag patterns; integration tests cover critical query counts.

## Operations

The API never runs privileged host commands. It writes owner-only JSON requests to an unprivileged inbox. Root-owned systemd runners claim requests through no-follow descriptors and publish world-readable status files without exposing secrets.
