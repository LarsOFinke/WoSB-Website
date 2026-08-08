# Working Guide for Repository Agents

This file applies to the entire repository. More specific rules in an `AGENTS.md`
located deeper in the tree take precedence for that subtree. Binding technical
details are defined in [docs/development/QUALITY_STANDARDS.md](docs/development/QUALITY_STANDARDS.md) and the
architecture documents linked there.

> **Agent quick start:** Before a broad repository analysis, first read
> [`.agents/ONBOARDING.md`](.agents/ONBOARDING.md) and run
> `bash .agents/scripts/project-context.sh`. The entry point references the
> maintained project cache, known failure patterns, and scope-dependent checks so
> already-established architecture does not have to be rediscovered.

## Working approach

1. Before making changes, read the affected flow, its callers, tests, configuration,
   and documentation. For cross-cutting tasks, create a short plan first.
2. Preserve existing changes that are unrelated to the task. Do not reset,
   overwrite, or commit other people's changes without being asked.
3. Implement the smallest functionally complete solution. Reuse existing
   abstractions and introduce new ones only when they genuinely clarify
   responsibility, lifecycle, or replaceability.
4. Fix root causes instead of hiding symptoms. Always consider security, privacy,
   migration, and operational consequences as well.
5. Run focused tests first, then the appropriate repository gates. Document changed
   behavior and new operational procedures in the same work step.

## Architecture and source code

- Backend domains remain separated below `spring-api/src/main/java/eu/royalblackwater/api/<domain>/`
  into `controller`, `filter`, `service`, `mapper`, `dto`, `entity`, and `repository`.
  Generic `model` packages are not permitted: domain-module transfer and value objects
  belong in `<domain>/dto`, persistence types in `<domain>/entity`, and declarative catalogs
  in the responsible service or repository layer. Generated API interfaces define only the
  HTTP contract; controllers bind requests and delegate directly to services. Business logic,
  authorization, and transactions belong in services, while persistence belongs exclusively
  behind module repositories. SQL definitions live in module-specific `repository/queries`
  catalogs; SQL in services is not permitted. Generated transport DTOs live exclusively under
  `api/dto`; domain-module transfer objects live under `<domain>/dto`. Controllers and public
  service boundaries must not expose entities, database rows, or raw maps. Only mappers translate
  between API DTOs, internal DTOs, entities, and repository rows.
- Dependencies are injected through constructors. Field injection and service locators are not
  permitted. Small, pure functions do not need a Spring bean lifecycle.
- Frontend pages orchestrate. Reusable presentation belongs in components, state and flows in
  composables, and network access in API modules.
- Infrastructure scripts orchestrate robust, idempotent helpers. Critical file changes should be
  atomic whenever possible; failures must return an unambiguous exit code and an actionable message.
- A file has one clearly nameable primary responsibility that is evident from its name. At roughly
  300–400 lines, consider splitting it into orchestrator, service, helper, transport, or data catalog.
  The automated upper limit for executable responsibilities is generally 420 lines; justified,
  cohesive declarative catalogs are not an invitation to create more catch-all files.
- Prefer KISS over speculative generalization; apply SOLID pragmatically. Do not add wrappers,
  managers, or base classes without at least one concrete maintainability benefit.
- Change the database schema only with immutable Flyway migrations. Review model, migration,
  upgrade, and recovery paths together; Hibernate remains set to `validate`.

## Frontend, security, and privacy

- For CSS, responsive behavior, accessibility, and design tokens, follow
  [docs/reference/CSS_ARCHITECTURE.md](docs/reference/CSS_ARCHITECTURE.md).
- Permissions are enforced server-side. Frontend guards are UX only.
- Do not place secrets, tokens, personal data, or complete IP addresses in source code,
  fixtures, logs, webhooks, or error messages.
- New personal data requires a purpose, legal/operational basis, retention policy, and
  export, correction, and deletion paths.
- Webhooks are concise audit and action notifications, not a surveillance mechanism.
  Delivery must not be able to block the primary business flow uncontrollably.

## Checks and completion

Run focused tests during development. Before completing a cross-cutting change, run the
following where locally available:

```bash
make validate
```

At minimum, the directly affected linters and tests as well as
`python3 infrastructure/scripts/quality/check_repository.py --strict-tree` must pass. Do not
version generated artifacts (`dist`, caches, virtual environments, local `.env` files, and
operational data), and do not edit generated files by hand.

A task is complete when implementation, migration/configuration, error handling, tests, and
documentation are consistent. Commit or push only when explicitly requested; never rewrite
someone else's history.
