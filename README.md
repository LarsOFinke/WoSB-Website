# Blackwater Mercenaries Hub

A fullstack fleet portal with a reproducible Raspberry Pi deployment.

```text
frontend/       Vue 3 + Vite application
backend/        FastAPI + SQLAlchemy application
infrastructure/ Docker Compose, PostgreSQL, NGINX, TLS, monitoring and Pi bootstrap
docs/           architecture, database and operations documentation
```

## One-command Raspberry Pi alpha deployment

After installing Raspberry Pi OS/Debian and cloning the repository:

```bash
cd ~/repositories/blackwater-hub
sudo ./setup.sh --profile full
```

This installs and configures Docker, PostgreSQL 16, Alembic migrations, the FastAPI backend,
the built Vue frontend behind NGINX, self-signed HTTPS, UFW, systemd startup, backups and
optional Uptime Kuma monitoring. With the `full` profile, the monitoring UI is published through NGINX at `https://<PI-IP>:8443`.

Read [`docs/FIRST_RUN.md`](docs/FIRST_RUN.md) and
[`infrastructure/README.md`](infrastructure/README.md).

## Dual database strategy

### Local development: SQLite

```bash
cd backend
cp .env.example .env
# set a strong SEED_ADMIN_PASSWORD
python -m venv .venv
. .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .[dev]
blackwater-dev
```

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

SQLite uses `DB_SCHEMA_MODE=create`, so local schema creation stays zero-maintenance.

### Server deployment: PostgreSQL

The infrastructure setup generates a PostgreSQL connection and uses
`DB_SCHEMA_MODE=migrate`. Alembic owns every production schema change; the API never runs
prototype `create_all()` migrations in production.

See [`docs/DATABASE_MODES.md`](docs/DATABASE_MODES.md).

## Access model

Public routes:

```text
/             fleet portal
/login
/register
/builds
/builds/:id
```

Authenticated routes include profile, guides, groups, calendar, forum and fleet management.
The staff panel requires staff privileges. Frontend guards and backend dependencies enforce the
same boundary.

## Common operations

```bash
make test
make build
make infra-status
make infra-logs
make infra-backup
make infra-update
```

## Health endpoints

```text
GET /api/health        process metadata
GET /api/health/ready  database readiness
```

## Current alpha boundaries

The stack is suitable for a private/LAN alpha and as a production foundation. Before a public
internet launch, replace the self-signed certificate with a trusted certificate, configure
off-host encrypted backups, add rate limiting and security scanning, and review SSH/network
hardening.
