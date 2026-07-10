# Admin Dashboard

This pass turns the admin area into an operational dashboard instead of a simple maintenance panel.

## Access review

Public registration no longer creates an immediately usable `users` row. The flow is now staged:

1. `POST /api/auth/register` creates a `registration_requests` row with status `pending`.
2. The applicant cannot sign in yet because no user account exists.
3. Admins review requests under **Admin → Access review**.
4. Approval creates the real `users` and `user_profiles` rows.
5. Fleet membership is requested separately after approval and login.
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
- resolved client IP
- forwarded IP
- user-agent
- query string
- exception text when available

The dashboard exposes:

- `GET /api/admin/logs/summary`
- `GET /api/admin/logs`

Logging persistence is configured in `backend/config/app.toml`. The DB handler is attached only to the app logger tree to avoid noisy dependency logs and SQL logging storms.


## Account hierarchy

Site roles are normalized in `site_roles`. Moderators cannot change, deactivate or demote administrators. Account mutation is rank-checked server-side; the frontend merely mirrors that policy.
