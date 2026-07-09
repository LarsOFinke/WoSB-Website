# Admin Dashboard

This pass turns the admin area into an operational dashboard instead of a simple maintenance panel.

## Access review

Public registration no longer creates an immediately usable `users` row. The flow is now staged:

1. `POST /api/auth/register` creates a `registration_requests` row with status `pending`.
2. The applicant cannot sign in yet because no user account exists.
3. Admins review requests under **Admin → Access review**.
4. Approval creates the real `users` and `user_profiles` rows.
5. If a planned fleet was selected, a pending `fleet_memberships` row is created and linked through `user_profiles.primary_fleet_membership_id`.
6. Rejection marks the request as `rejected` and does not create a user.

This keeps account state simple: an accepted registration is a user; a pending registration is not.

## Persisted logs

Application/request logs are persisted in `app_logs` via the central `app` logger tree.

Stored fields are intentionally compact:

- timestamp
- level
- logger
- message
- request id
- method/path/status
- duration in milliseconds
- client host
- exception text when available

The dashboard exposes:

- `GET /api/admin/logs/summary`
- `GET /api/admin/logs`

Environment flags:

```env
DB_LOGGING_ENABLED=true
DB_LOG_LEVEL=INFO
```

The DB handler is attached only to the app logger tree to avoid noisy dependency logs and SQL logging storms.
