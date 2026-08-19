# System architecture

The responsibilities and diagnostic entry points of every backend, frontend, and
infrastructure module are consolidated in the [module catalog](MODULE_CATALOG.md).

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

`openapi/source/` is the versioned, modular external HTTP specification. `openapi/openapi.json` is its deterministic assembled compatibility artifact. The DTO
generator creates immutable transport records under `api/dto`; it does not create
a runtime contract layer. Module-owned `@RestController` classes own their Spring
MVC mappings and bind/validate generated request DTOs directly.
`audit_controller_contract.py` compares all 189 controller routes, parameters,
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

## Derived build-print cache

Build printouts are derived data and have a separate lifecycle from business
build state. The browser creates a deterministic SVG source and hashes it with an
explicit renderer version; the resulting key identifies the visible render while
`builds.updated_at` identifies the business revision. The server accepts a cache
write only for the still-current business revision and serializes writes on the
build row.

The active database metadata points to a checksum-versioned PNG. The new file is
written before the database commit, rollback removes it, and commit removes the
previous file. Downloads require the cache key in the URL, so browser HTTP caches
are version-addressed as well. A build mutation clears the active cache metadata;
a scheduled reconciler removes stale metadata, legacy/orphan files and abandoned
temporary writes with a grace window for in-flight transactions.

The cache is shared across users but is not an authorization bypass: authenticated
viewers may reuse a valid cache entry, while only the build owner or staff may
populate or repair it because the server does not independently rasterize and
compare the client-produced PNG. Printouts consume the same global storage budget
and minimum-free-space reserve as ordinary uploads. Only one cache variant is
active per build, deliberately bounding persistent storage; locale or renderer
variants may replace each other rather than accumulate.

## Port-Battle strategy documents

Strategies keep an owned uploaded image as an immutable visual background and a
versioned JSON document as the independently editable SVG overlay. The overlay
contains ship markers, optional player labels, website build and guide references,
freehand paths, lines, arrows, formations, and text. Build references are validated
as `(build, marker ship)` pairs rather than merely as independently existing IDs.
The browser applies the same compatibility rule when presenting build choices.

The editor maps pointer positions through the SVG screen transformation into its
normalized viewBox coordinates, so drawing and dragging remain aligned when the
chart is responsive or letterboxed. A separate legend below the chart carries build
and guide details for readable screen and print output. Strategies are private and
owner-controlled by default; publication creates a revocable, non-sequential public
identifier and exposes the associated background only while a published strategy
references it. Shared routes are read-only.

SVG export fetches the authorized background and embeds it as a data URL alongside
inlined SVG presentation properties, producing one portable file instead of retaining
an authenticated API reference. Browser printing uses a fixed two-section document:
the briefing and chart occupy the first landscape page, and the player/build/guide
legend starts on the second page with entries kept intact where space permits.

## Persisted image optimization

The files boundary optimizes validated JPEG and PNG uploads before their final
path and database size are committed. This applies uniformly to strategy
backgrounds, guide and forum attachments, general uploads, and master-data
images. Derived build-print PNGs use the same optimizer before checksums and
quota accounting are calculated. Images are bounded to 4096 pixels on their
longest edge, decode work is capped, JPEG metadata/orientation is normalized,
and an optimized rewrite replaces the source only when it is smaller or a
dimension reduction is required. GIF and WebP files remain byte-preserved
because the JDK does not provide a safe animation-capable rewrite path.
