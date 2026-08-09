# Contributing

All contributions must follow the [quality standards](docs/development/QUALITY_STANDARDS.md) and the
[repository working guide](AGENTS.md).

1. Prefer small, functionally complete changes.
2. Change the database schema only through immutable Flyway migrations.
3. Maintain master data using stable `seed_id`, revision, and checksum values.
4. Always test API permissions server-side; frontend guards are convenience only.
5. Do not add a new large page or service file without a clear reason. At roughly 300–400 lines,
   consider whether a data catalog, calculation, API access layer, or UI section is a separate responsibility.
6. Before opening a pull request, run:

```bash
make validate
```

Commits and pull requests should state the problem, solution, migration/seed impact, and test evidence.

`patches/` is a local transfer/download workspace. Patch payloads in that directory are intentionally ignored by Git; the committed source tree and changelog are the authoritative project history. Keep only `patches/.gitkeep` versioned.
