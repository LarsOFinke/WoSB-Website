# Fleet Home, Group Signups and DB Logging

## Fleet portal as home

The public root route (`/`) now opens the official fleet portal instead of a generic marketing home page. The previous `/home` route redirects to `/`.

The fleet portal remains public and contains the official fleet overview plus a direct application entry point. Visitors who are not signed in can start the application flow through registration with the official fleet application already selected.

## Group search signups

Group search posts support an optional scheduled time window:

- `scheduled_start_at`
- `scheduled_end_at`

The end time is optional, but if both fields are present the end time must be after the start time.

Users can sign up for open group searches. A signup can include:

- display name
- optional fleet note
- optional ship
- optional saved build owned by the signed-in user
- optional note for the group lead

When a build is linked, the backend derives the ship and ship rate from that build. The backend validates that:

- the group is open and not full
- the user is not already signed up
- guest signup is only possible when enabled on the group
- linked builds belong to the signed-in user
- selected ships/builds match the group ship-rate requirements

## Logging policy

Application/request logs are persisted in `app_logs` and shown in the Admin Dashboard. Backend console request logging is disabled by default via:

```env
CONSOLE_LOGGING_ENABLED=false
DB_LOGGING_ENABLED=true
```

Stored request metadata includes:

- request ID
- method
- path
- status code
- duration
- direct client host
- resolved client IP
- `X-Forwarded-For`
- user agent
- query string
- exception text, if present

For deployments behind a proxy, `client_ip` prefers `X-Forwarded-For`, then `X-Real-IP`, and finally the direct client host.
