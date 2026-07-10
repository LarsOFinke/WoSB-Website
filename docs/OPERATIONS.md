# Operations and Local Development

## Local start

Backend:

```bash
cd backend
cp .env.example .env
# edit .env and set a strong SEED_ADMIN_PASSWORD
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .[dev]
rbf-seed --reset
rbf-dev
```

Frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Validation checklist

Frontend:

```bash
npm run check:locales
npm run build
npm audit --omit=dev
find src -name '*.js' -print0 | xargs -0 -n1 node --check
```

Backend:

```bash
python -m compileall -q backend/src
```

## Logging

Routine request/application logs are stored in the database and surfaced in the Admin Dashboard. Console logging is controlled by `backend/config/app.toml` and is disabled by default. Every response includes `X-Request-ID`; preserve this value when reporting bugs.

## Database reset

The database URL comes from `backend/.env`. For the local SQLite setup:

```bash
cd backend
rbf-seed --reset
```

For production, use PostgreSQL plus Alembic migrations before real user data.

## Uploads

The upload directory comes from `UPLOAD_DIR` in `backend/.env` and is served through `/uploads`. The repository keeps only one local demo upload tree at `backend/storage/uploads/demo`; do not create a second root-level `storage/uploads` tree. Current safety checks include file type allow-listing, empty-file blocking and size limits by media type from `backend/config/app.toml`.


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.

## PostgreSQL meldet `password authentication failed`

Aktuelle Versionen starten Compose mit einer expliziten `--env-file`-Angabe und
entfernen gleichnamige Variablen aus der Host-Shell. Bei einem Upgrade von einer
betroffenen Alpha-Version muss ein noch unbenutzter, fehlgeschlagen
initialisierter Cluster einmal entfernt und anschließend das Setup erneut
ausgeführt werden. Produktivdaten dürfen dabei nicht ohne Backup gelöscht
werden.

## Git and runtime data permissions

`infrastructure/data/` is intentionally not tracked. The setup creates all required
subdirectories and assigns them to the container service UIDs. Do not add `.gitkeep`,
`.gitattributes`, or other tracked files below this path; otherwise normal non-root
`git pull` and `git reset` operations can fail after deployment.

## Shell execution and CI portability

Operator entrypoints (`setup.sh`, `update.sh`, `scripts/validate.sh`, and
`infrastructure/setup.sh`) are tracked as executable. Internal invocations and
systemd units call scripts through `/usr/bin/env bash`, so copied validation
trees and filesystems that do not preserve Unix mode bits do not fail with exit
code 126.
