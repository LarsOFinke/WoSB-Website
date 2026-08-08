# Authentication and API Contract Review, August 7, 2026

## Reason

After the Spring layer/DTO restructuring, production login with the supposed first-run credentials
returned HTTP 401. The entire chain from browser request through OpenAPI, generated DTOs, and controller
to bootstrap initialization and password verification was therefore reviewed again.

## Login review result

The login request was already synchronized: frontend, `LoginRequest`, generated `AuthApi`,
`AuthController`, and `AuthService` consistently use the fields `username` and `password`. Password
verification also supports the PBKDF2 format used by the previous backend. The PostgreSQL integration
test successfully logs in a freshly created bootstrap administrator with the configured first-run password.

A 401 with an existing dataset therefore does not mean the login DTO fields are swapped.
`SEED_ADMIN_PASSWORD` is deliberately only the secret for initial user creation. If a bootstrap admin
already exists, its current password hash is not overwritten from the environment file on restarts or deployments.

## Contract drift found

The OpenAPI contract still contained the old generic validation-error format: 172 operations documented
HTTP 422 with a structured `HTTPValidationError` response, although Spring Bean Validation and binding
failures return HTTP 400 with a public `detail` text. Login also did not document its real HTTP 401 case.

The contract now uses `ApiError` with `detail` as the shared public error representation. The 172 generic
validation responses are HTTP 400. HTTP 422 remains explicitly only for six semantically business-specific
validations. `POST /api/auth/login` documents 200, 400, and 401 with the schemas actually used.

## First-run invariant

Fresh installations verify the generated `SEED_ADMIN_USERNAME`/`SEED_ADMIN_PASSWORD` after readiness
through the public login API. A mismatched user or password hash aborts activation. Updates of existing
installations do not run this check so a later-changed administrator password is never tested against or
reset to the old seed secret.

## Release baseline

After the architecture cutover, the product version is deliberately reset to `1.0.0`. Maven, frontend,
OpenAPI, reference, and deployment versions are aligned again to this shared baseline. Further compatible
fixes start at `1.0.1`.
