# Repository Cleanup, August 6, 2026

## Goal

After the layer and DTO refactoring, the repository was reviewed for orphaned packages,
dead classes, empty source directories, obsolete helper abstractions, and inconsistent
module assignments. The cleanup changes no API routes or business contracts; it sharpens
the existing architecture:

```text
Controller -> Service -> Repository
                  |          |
                  v          v
                Mapper <-> DTO / Entity / database row
```

## Cleaned structures

- All generic module `model` packages were removed.
- Internal build and security transfer objects now live in functionally explicit module
  `dto` packages.
- The generated build-stat catalog now lives as a service-owned domain catalog in the
  builds module; the generator writes directly into that target package.
- The master-data seed catalog lives in the repository layer.
- The webhook event catalog lives in the service layer and uses an internal DTO translated
  through a mapper.
- The empty `account/model` directory and all other empty Java source directories were removed.
- The unused `SiteRoleRepository` was deleted.
- Time-scoped refactoring reports were consolidated under `docs/development/reviews/`
  instead of remaining as loose files in the repository root.

## Cleaned code paths

- Remaining controller calls to the already-removed generic `body(body, Type.class)` helper
  were converted to typed request DTOs.
- Dead controller and parameter helpers were removed.
- The obsolete `RequestParameters` intermediate step was deleted.
- Controllers no longer convert typed query parameters into `Map<String, Object>`. Module
  filters receive concrete values such as `String`, `Long`, `boolean`, `limit`, and `offset`.
- Redundant local `AuthenticatedUser` variables were removed where only the authentication
  check was needed; `CurrentUser.require()` remains as an explicit security boundary.
- Imports and tests were adjusted to the unambiguous package responsibilities.
- The repository cleanup script no longer uses a contradictory `find -prune`/`-delete` path
  for file artifacts; `make clean` again completes the hygiene run reliably with success.

## New regression gates

The Spring architecture audit now additionally blocks:

- generic `model` packages in business modules;
- empty Java source directories;
- the removed `RequestParameters` helper;
- raw parameter maps and old body casts in controllers;
- module repositories without application consumers.

Existing rules for typed API boundaries, mapper responsibility, service/repository separation,
SQL placement, and complete OpenAPI coverage remain in place.

## Validation

Successfully verified:

- 177 OpenAPI operations across 34 generated API interfaces and 26 module controllers;
- 179 generated API DTOs against the current OpenAPI contract;
- Spring architecture audit across 465 production Java sources;
- Java syntax and internal package/import graph;
- documentation, cache, infrastructure, and strict-tree gates;
- recovery test package with 8 passing tests;
- 157 dependency-free frontend tests plus the build-designer regression.

## Environment limits

Maven was not installed in the provided execution environment and could not be installed
because external DNS/network access was unavailable. Therefore `mvn verify`, full Spring
context starts, and PostgreSQL Testcontainers were not run here.

The complete frontend gate reaches the SFC step after the 157 dependency-free tests and the
build-designer regression, but cannot continue there without installed `node_modules` or
`@vue/compiler-sfc`. Generated and ignored frontend locale files plus all Python and pytest
caches were removed before delivery.
