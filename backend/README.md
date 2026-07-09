# Backend

FastAPI backend for Iron Crown Fleet Hub.

## Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
wosb-seed --reset
wosb-dev
```

API health check:

```text
http://127.0.0.1:8000/api/health
```

## Layout

```text
src/app
├── api/routes      HTTP routes and auth dependencies
├── core            config, security, constants, logging, middleware, errors
├── db              SQLAlchemy session, create/reset, seeds
├── models          SQLAlchemy models and relationships
├── schemas         Pydantic request/response contracts
└── services        business logic and transactional operations
```

## Logging

Logging is configured centrally in `app.core.logging`. Every request is logged by `RequestLoggingMiddleware` and every response includes `X-Request-ID`.

Environment variables:

```text
LOG_LEVEL=INFO
LOG_FORMAT=plain   # plain or json
SQL_LOG_LEVEL=WARNING
```

Do not log passwords, raw session tokens or file contents.

## Data model

The schema is normalized around users/profiles/fleet memberships, builds/build slots/build effects, guides/build references/files and forum post attachments. See `../docs/DATABASE_SCHEMA.md` and `../docs/BACKEND_ARCHITECTURE.md`.

## Development admin

```text
admin / admin123
```

Override via `.env`/environment variables before deployment.

## Production notes

Before production, add Alembic migrations and move from SQLite to PostgreSQL. See `../docs/PRODUCTION_CHECKLIST.md`.


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.


## Single Fleet Refactor

Der Flottenbereich arbeitet jetzt mit genau einer offiziellen Iron Crown Fleet. Registrierung, Profil und Flottenverwaltung referenzieren dieselbe zentrale Membership. Details stehen in `docs/SINGLE_FLEET_REFACTOR.md`.

## Build Designer catalog checks

Ship and upgrade seeds are validated before seeding via `app.db.seeds.build_catalog_quality`. Build stat rows are calculated centrally in `app.services.build_stat_service`.

## Build Designer Waffen/Special Crew

- Special Crew ist Teil des Build-Katalogs und wirkt über normalisierte `build_item_effects` in die Stat-Vorschau.
- Waffenoptionen besitzen Slot-Metadaten (`option_kind`, `allowed_slot_types`, `weapon_caliber_inches`).
- Der Mörser-Slot ist separat validiert; Mortars können nur dort und nur bis zum Schiffskaliber-Limit gesetzt werden.
- Details: `docs/BUILD_DESIGNER_WEAPONS_AND_CREW.md`.

## Latest foundation update

- `/` now opens the official fleet portal and `/home` redirects there.
- Group search supports optional time windows, member signup, ship selection and optional saved-build linking.
- Request logs are stored in the database/Admin Dashboard; backend console logging is disabled by default while IP, forwarded IP, user-agent and query metadata are persisted.
- See `docs/FLEET_HOME_GROUP_SIGNUPS_LOGGING.md` for details.
