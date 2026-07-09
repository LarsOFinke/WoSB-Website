# Operations and Local Development

## Local start

Backend:

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .[dev]
wosb-seed --reset
wosb-dev
```

Frontend:

```bash
cd frontend
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

Default local logs are plain text. For structured logs:

```bash
LOG_FORMAT=json LOG_LEVEL=INFO wosb-dev
```

Every response includes `X-Request-ID`. Preserve this value when reporting bugs.

## Database reset

The prototype uses SQLite by default:

```bash
cd backend
wosb-seed --reset
```

For production, use PostgreSQL plus Alembic migrations before real user data.

## Uploads

Uploads are stored under `backend/storage/uploads` by default and served through `/uploads`. Current safety checks include file type allow-listing, empty-file blocking and size limits by media type.


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.
