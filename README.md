# Royal Blackwater Vanguards [RBV]

A full-stack fleet operations hub with a reproducible Raspberry Pi deployment.

```text
frontend/       Vue 3 + Vite application
backend/        FastAPI + SQLAlchemy application
infrastructure/ Docker Compose, PostgreSQL, NGINX, TLS, monitoring and Pi bootstrap
docs/           architecture, database and operations documentation
```

## Production domain

The production default is:

```text
https://royal-blackwater-vanguards.eu
```

Before requesting a public certificate, the domain's DNS record must resolve to the server's
public IP and TCP ports 80 and 443 must be forwarded to the Pi.

## One-command Raspberry Pi deployment

After installing Raspberry Pi OS/Debian and cloning the repository:

```bash
cd ~/repositories/royal-blackwater-vanguards
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-vanguards.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-vanguards.eu
```

The setup installs Docker and Compose, creates production secrets, starts PostgreSQL 16,
runs Alembic migrations and idempotent seeds, builds the FastAPI/Vue images, configures NGINX,
requests a Let's Encrypt certificate, enables renewal, configures UFW, installs systemd startup
and backup jobs, and starts optional Uptime Kuma monitoring.

When DNS or public port forwarding is not ready yet, use `--tls-mode auto`. The stack starts
with a self-signed bootstrap certificate and attempts Let's Encrypt without blocking the LAN
installation.

Read [`docs/FIRST_RUN.md`](docs/FIRST_RUN.md),
[`docs/PRODUCTION_CHECKLIST.md`](docs/PRODUCTION_CHECKLIST.md) and
[`infrastructure/README.md`](infrastructure/README.md).

## Dual database strategy

### Development: SQLite

```bash
cd backend
cp .env.example .env
# set a strong SEED_ADMIN_PASSWORD
python -m venv .venv
. .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .[dev]
rbv-dev
```

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

SQLite uses `DB_SCHEMA_MODE=create`, keeping local development dependency-free.

### Production: PostgreSQL

The infrastructure setup generates the PostgreSQL connection and uses
`DB_SCHEMA_MODE=migrate`. Alembic owns every production schema change; the API never invokes
prototype `create_all()` behavior in production.

## Access model

Public routes:

```text
/             Fleet Portal
/login
/register
/builds
/builds/:id
```

Profile, guides, groups, calendar, forum and fleet management require a login. The Staff Panel
requires staff privileges. Frontend guards and backend dependencies enforce the same boundary.

## Web access

```text
https://royal-blackwater-vanguards.eu       RBV Fleet Hub
https://royal-blackwater-vanguards.eu:8443  Uptime Kuma (full profile)
```

Keep port 8443 restricted to LAN/VPN unless a public monitoring interface is explicitly desired.
PostgreSQL remains loopback-only on port 15432.

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

## Release 0.11 design pass

The RBV rebrand includes two UI iterations: first, a scalable brand lockup and clearer workspace
navigation; second, improved hierarchy, interaction states, responsive layouts, keyboard behavior
and reduced-motion support. The fleet, profile and staff workspaces share the same visual system.
