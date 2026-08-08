# JSON Sources and Catalogs

Hand-maintained JSON data follows the same KISS/SOLID boundaries as source code: one file
has one clearly recognizable responsibility, changes should produce small diffs, and large
catch-all documents are not used as the authoring format.

## OpenAPI

The canonical authoring source lives under `openapi/source/`:

- `root.json` contains only OpenAPI metadata,
- `schemas/<SchemaName>.json` contains exactly one schema,
- `operations/<operationId>.json` contains exactly one method with path and operation.

`openapi/openapi.json` is the deterministically assembled compatibility artifact for
generators, audits, and external tooling. It is not edited by hand.

```bash
python3 infrastructure/scripts/generation/assemble_openapi.py
python3 infrastructure/scripts/generation/generate_api_dtos.py
python3 infrastructure/scripts/generation/generate_api_reference.py
```

`assemble_openapi.py --check` fails on duplicate operations, `operationId` filenames that
do not match, or a stale assembled contract.

## Build-stat catalog

`spring-api/src/main/reference/build-stats/` contains exactly one stat definition per file.
The numeric prefix preserves the functional order; the stable key in the filename makes the
responsibility visible. `BuildStatCatalog.java` remains a generated runtime artifact.

```bash
python3 infrastructure/scripts/generation/generate_build_stat_catalog.py
```

## Seed catalogs

Large build-option and ship-rate files are split into individual seed entries:

- `seed/builds/options/<category>/<NNN-seed-id>.json`,
- `seed/ships/rates/<rate>/<NNN-seed-id>.json`.

A file prefix defines only the established stable catalog order; functional identity remains
`seed_id`. Spring loads the entries directly and exposes them as read-only maps.
`seed/manifest.json` references catalogs through globs instead of monolithic files.

## Size gate

Hand-maintained JSON files under the OpenAPI source, reference catalogs, seeds, and frontend
test fixtures may contain at most **420 lines**. Generated compatibility files such as
`openapi/openapi.json` and lockfiles are deliberately exempt. The gate lives in
`infrastructure/scripts/quality/check_repository.py`.
