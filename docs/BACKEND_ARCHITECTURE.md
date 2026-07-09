# Backend Architecture

## Layers

### API routes

Routes live in `backend/src/app/api/routes`. They should only handle:

- HTTP method/path definitions.
- Dependency injection for DB/session/current user.
- Converting service errors into HTTP errors.
- Request and response schemas.

### Services

Services live in `backend/src/app/services`. They own business logic such as:

- Build validation.
- Fleet application and approval flows.
- Guide/forum embed validation.
- Upload validation.
- Calendar permissions.

Services should be callable from route handlers, seeds and future tests without HTTP objects.

### Models

Models live in `backend/src/app/models`. They describe persistence and safe computed properties. New schema work should stay normalized by default.

### Schemas

Schemas live in `backend/src/app/schemas`. They define API contracts and input validation. Do not leak SQLAlchemy models directly to frontend code.

### Core

Core contains cross-cutting infrastructure:

- `config.py`: environment-backed settings.
- `security.py`: password/session token helpers.
- `dependencies.py`: auth dependencies.
- `constants.py`: stable enum-like constants.
- `logging.py`: central log configuration.
- `middleware.py`: request logging/request IDs.
- `errors.py`: shared application error response shape.

## Logging

Application logging is configured once in `app.core.logging.configure_logging()`. Request logging is handled by `RequestLoggingMiddleware` and returns `X-Request-ID` on every response.

Environment variables:

- `LOG_LEVEL`: defaults to `INFO`.
- `LOG_FORMAT`: `plain` or `json`.
- `SQL_LOG_LEVEL`: defaults to `WARNING`.

Use module loggers in new code:

```python
import logging

logger = logging.getLogger(__name__)
```

Do not log passwords, raw session tokens or uploaded file contents.

## Database standards

- Every table has a single primary key except intentional one-to-one profile table `user_profiles`.
- Many-to-many/domain references use join tables.
- Repeated option effects are stored in `build_item_effects`, not JSON blobs.
- Guide build links are stored in `guide_build_references`.
- Uploaded file metadata is stored in `stored_files`; binary content is externalized.
- Check constraints protect enum/range fields on newly created schemas.

## Transaction standards

Current prototype services commit internally for simplicity. Future production work should move toward explicit unit-of-work boundaries per route/service command, especially when adding migrations and tests.


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.
