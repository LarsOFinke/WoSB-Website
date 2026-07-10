# Release 0.17.0 — Permissions, normalized catalogs and production seed cleanup

- Introduces normalized site, fleet and squad role catalogs with authority ranks and capability flags.
- Prevents moderators and peer accounts from disabling or demoting administrators.
- Displays active Fleet Admirals and Fleet Lieutenants consistently as fleet leadership.
- Normalizes preferred ships, weapon classes, weapon mount arcs and option-slot compatibility.
- Removes generic demo activity from production seeds and conservatively retires untouched historic fixtures.
- Adds curated official Russia → Essex/La Creole → Poltava → Victory templates and linked guides.
- Replaces the default New Captain content with a five-phase progression path while preserving staff-created blocks.
- Adds Alembic revision `7e4c9b2a1f60`; deployment requires `--migrate --seed` and does not reset PostgreSQL.
