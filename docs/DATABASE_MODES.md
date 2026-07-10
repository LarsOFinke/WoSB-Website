# Database modes

Blackwater supports two explicit database lifecycles.

## Development: SQLite

```env
APP_ENV=development
DATABASE_URL=sqlite:///./storage/blackwater-hub.db
DB_SCHEMA_MODE=create
```

`DB_SCHEMA_MODE=create` lets the application create tables on startup and run the small
SQLite compatibility migrations used by existing local prototype databases. This mode is
optimized for a quick local start and tests.

```bash
cd backend
cp .env.example .env
pip install -e .[dev]
blackwater-dev
```

## Production: PostgreSQL

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://blackwater:<secret>@postgres:5432/blackwater
DB_SCHEMA_MODE=migrate
```

Production schema ownership belongs to Alembic. The application does not call
`Base.metadata.create_all()` in this mode. The container sequence is:

```text
postgres healthy -> alembic upgrade head -> idempotent seed -> API start
```

Manual migration commands:

```bash
cd backend
alembic current
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Never use `blackwater-seed --reset` in production. The command is blocked when
`APP_ENV=production`.

## Why the distinction matters

SQLite is ideal for a zero-dependency developer workflow, but its file locking and migration
characteristics are not the desired server runtime. PostgreSQL provides concurrent access,
stronger operational tooling and reliable dumps/restores. Keeping the modes explicit prevents
prototype schema helpers from silently modifying a production database.
