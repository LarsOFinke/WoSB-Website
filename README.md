# Royal Blackwater Fleet [RBF]

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
https://royal-blackwater-fleet.eu
```

Before requesting a public certificate, the domain's DNS record must resolve to the server's
public IP and TCP ports 80 and 443 must be forwarded to the Pi.

## One-command Raspberry Pi deployment

After installing Raspberry Pi OS/Debian and cloning the repository:

```bash
cd ~/repositories/royal-blackwater-fleet
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
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
rbf-dev
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
/fleet
```

Profile, the New Captain Guide, builds, guides, temporary group searches, fleet squads, calendar,
forum and fleet management require a login. The Staff Panel requires staff privileges. Frontend
guards and backend dependencies enforce the same boundary.

## Web access

```text
https://royal-blackwater-fleet.eu       RBF Fleet Hub
https://royal-blackwater-fleet.eu:8443  Uptime Kuma (full profile)
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

## Release 0.12: newcomer-first fleet hub

The Royal Blackwater Fleet release aligns the public portal with the fleet's real operating model:
newcomer onboarding through guides and proven builds, persistent Q&A in the forum, transparent
event planning through the calendar and clear Discord voice expectations for competitive content.
All public portal standard copy is explicitly localized in all seven supported languages.

Main activity is communicated as 12:00–02:00 CET, with Port Battle focus between 18:00 and
23:00 CET. Discord voice is mandatory for Port Battles and other competitive operations; it is
optional but encouraged for normal fleet activity.


## Release 0.13.5 — CI mode portability

The validator no longer fails solely because a checkout lost Unix executable
bits. CI and internal delegation invoke entrypoints through `bash`; validation
checks file presence, Bash shebangs and syntax instead. Operator entrypoints are
still shipped with executable permissions in the canonical repository.


## Release 0.14.0 — Build Designer audit and New Captain Guide

This release audits every seeded ship weapon layout using an explicit bow–broadside–stern
format, normalizes weapon options to their dedicated ship arcs and prevents duplicate upgrades
server-side as well as in the editor. The Build Designer now hides zero-capacity weapon groups,
weapons that do not belong to the selected arc and options already used in another slot.

Authenticated members receive a dedicated `/new-captain` roadmap. Staff can curate text sections
and ordered resource collections that link to guides, builds, internal modules or external sources.
The roadmap is also the first step of the Fleet Portal's New Captain Path.

## Release 0.15.0 — Public boundary and catalog completion

Anonymous visitors now see only the localized landing page and a compact public fleet overview.
Builds, ships, guides, forum, calendar, groups, the New Captain Guide and fleet management require
an authenticated account in both the Vue router and the API. The public fleet endpoint exposes a
small dedicated response model without pending applications, usernames or member-directory data.

The Build Designer seed catalog now has cross-category completeness checks. Lanterns, ship
upgrades and Specialists received audited, idempotent catalogs with current B20 naming, traceable
revision metadata and regression tests. Existing options that are no longer part of the active
catalog remain attached to historical builds but disappear from new-build selectors.


## Release 0.15.1 — Fleet-management access

Fleet Management is now shown only to administrators, moderators, active Fleet Admirals, and active Fleet Lieutenants. The frontend route and backend endpoints enforce the same policy.


## Release 0.15.2 — Seed compatibility hotfix

Fixes the `Fortified Ports` / `Reinforced Ports` demo-build mismatch and migrates legacy option references during idempotent seeding.

## Release 0.15.3 — Database-safe updates and monitoring recovery

Normal server updates now rebuild and recreate only the API and frontend gateway.
PostgreSQL is not started, recreated, migrated, seeded or dumped during a normal
code-only update. Changed Alembic migration files are detected after Git updates;
operators can also request `--migrate` explicitly. Seeds run only with `--seed`.

Uptime Kuma and its HTTPS monitoring gateway are ensured independently before
optional database work. A migration or seed failure can therefore no longer skip
the monitoring start step and leave port 8443 unavailable.

## Release 0.16.0 — Fleet squads and scoped calendar planning

The fleet can now be divided into permanent squads without granting their leaders global fleet
administration. Administrators, moderators, Fleet Admirals and Fleet Lieutenants create and
archive squads and appoint the first Squad Leader. Squad Leaders can maintain the unit profile,
roster, officers and private calendar entries; Squad Officers can support day-to-day roster and
calendar work without being able to seize command.

Fleet-wide calendar entries remain visible to every authenticated member. Squad entries are shown
only to members of that squad and to fleet/staff leadership. The release adds the `squads` and
`squad_members` tables plus a nullable squad scope on existing calendar events. No existing event
or membership data is replaced.

## Release 0.16.1 — Account/fleet separation and Build Designer cleanup

Registration now creates only a reviewable portal account. Fleet membership is requested later,
after approval and login, from the public fleet page. Pending applications and ordinary accounts
are intentionally excluded from Squad Leader, Officer and Member selection; only active members
of the official fleet are eligible.

The Build Designer no longer validates ammunition, consumables, hold cargo or Specialists as
weapons. Inventory selection now uses explicit immutable slot reconciliation, preserves the
selected item, adds the next empty slot predictably and keeps weapon arc validation limited to
actual weapon fields. A standalone frontend regression test covers item selection, quantities,
capacity limits and invalid-option removal.

## Release 0.16.2 — Personal squad workspace

Authenticated users now have a dedicated `/profile/squads` workspace (with `/my-squads` as an
alias) alongside My Builds and My Group Searches. It lists only explicit active squad assignments;
site or fleet administration permissions never create an implicit squad membership. The workspace
separates command responsibilities from ordinary memberships, shows each user's squad role,
member capacity, the next appointment per unit and a combined upcoming squad agenda. Leaders and
officers can open squad management and create scoped calendar entries directly.

The backend adds `GET /api/squads/mine` and exposes the current user's squad role in squad summaries.
The endpoint remains session-protected and deliberately excludes inactive memberships and unrelated
squads. No database migration or seed run is required for this release.

## Release 0.17.0 — Permission hierarchy, 3NF catalog cleanup and production onboarding

Site, fleet and squad roles now live in normalized definition tables with explicit authority ranks and
capabilities. Moderators cannot deactivate or demote administrators, and active Fleet Admirals and
Fleet Lieutenants are the single source for leadership displays on the landing page and in Fleet
Management.

The Build Designer now derives available weapons from normalized ship mounts, slot types and
Light/Medium/Heavy weapon classes instead of serialized layouts or a persisted eligibility cache.
Production seeding no longer creates fake Builds, groups, forum threads, calendar events or demo
uploads. It creates only required catalogs plus curated progression Builds/guides for the New Captain
path. Upgrade with `sudo ./update.sh --migrate --seed`; the PostgreSQL volume is retained and no
reset is performed.
