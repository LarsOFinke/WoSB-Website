# API usage and security

The versioned OpenAPI 3.1 specification at `openapi/openapi.json` is the
canonical machine-readable external API definition. The generated exhaustive
endpoint index is [API_ENDPOINTS.md](API_ENDPOINTS.md), and immutable Java
request/response DTO records derive from the same specification. Spring MVC
routing itself is module-controller-owned and checked back against OpenAPI by
`audit_controller_contract.py`; there is no generated runtime API-interface layer.

## Base URL and media types

- Browser and production clients use the same origin under `/api`.
- JSON requests use `Content-Type: application/json`; file operations use the
  multipart definitions from the contract.
- Successful delete operations may return `204 No Content`; clients must not
  attempt to parse an empty response body.
- `date` values use ISO `YYYY-MM-DD`; `date-time` values use ISO-8601 and may
  carry an offset such as the browser-produced UTC suffix `Z`. Controller-owned
  query bindings use explicit `DateTimeFormat` annotations instead of relying on
  the server locale.

## Authentication model

The browser API uses an opaque, high-entropy session token in the HttpOnly
session cookie configured by `rbf.session.cookie-name`. Only the SHA-256 token
hash is stored in PostgreSQL. Spring Security reconstructs authentication and
authorities for every request; the application does not use a servlet HTTP
session.

Clients send cookies with `credentials: include`. Do not copy session or consent
cookies into tickets, logs, examples or test fixtures. The backend intentionally
does not expose token contents to JavaScript.

## CSRF, host and origin boundary

Unsafe methods (`POST`, `PUT`, `PATCH`, `DELETE`) require the synchronizer token
from the readable `XSRF-TOKEN` cookie in the `X-XSRF-TOKEN` header. A client can
bootstrap that cookie with `GET /api/auth/me`, including when no user session is
present. Production mutations additionally pass the configured host/origin
boundary; CORS is allow-list based.

Example browser-equivalent flow:

```text
GET  /api/auth/me                   -> receive XSRF-TOKEN cookie
POST /api/auth/login                Cookie: XSRF-TOKEN=...
                                    X-XSRF-TOKEN: ...
                                    Content-Type: application/json
GET  /api/auth/me                   Cookie: rbf_hub_session=...
```

## Access classes

- Public health, registration, legal/privacy and explicitly public discovery
  endpoints are allow-listed in `SecurityConfiguration`.
- Member endpoints require an authenticated active user.
- Fleet/squad management is checked server-side against current memberships and
  role capabilities in domain services.
- Staff and administrator operations under `/api/admin/**` require the matching
  authority; frontend route guards are not a security boundary.
- Ownership checks for builds, guides, files, groups and forum content are domain
  rules and may be stricter than the path prefix suggests.

The OpenAPI snapshot does not duplicate dynamic authorization rules per endpoint.
For a security-sensitive change, inspect `SecurityConfiguration`, the owning
module controller and the domain service together.

## Errors and validation

JSON error responses use the OpenAPI-owned `ApiError` shape
`{ "detail": "..." }`. Bean-validation and binding failures are HTTP `400`;
HTTP `422` is reserved for the small set of operations whose service layer
rejects syntactically valid but semantically invalid input.

- `400` denotes malformed JSON or transport-level binding failures, including
  invalid date and timestamp query parameters.
- `401` denotes missing or invalid authentication.
- `403` denotes rejected authorization, CSRF, host or origin boundaries.
- `404` is used when a resource is unavailable to the caller.
- `409` denotes a state conflict such as a duplicate registration.
- `422` denotes semantically invalid input where defined by the operation.
- Unexpected failures return `500` and are logged centrally as `api_error`
  without request payloads or secrets.

Clients should primarily branch on HTTP status and the bounded public error
detail. Internal Java exception names and production log messages are not API.
For the safe route-to-controller/service diagnostic workflow see
[Module-oriented debugging](../debugging/MODULE_DEBUGGING.md).

## Pagination and filtering

Growing collections use the contract's bounded `search`, `limit`, `offset`, sort
and domain filter parameters. Clients must not assume an unbounded complete list
or invent undocumented query parameters. Defaults and maximums are defined by
the OpenAPI parameter schemas and enforced again by the backend.

## OpenAPI change workflow

1. Change and review `openapi/openapi.json`.
2. Regenerate API DTOs with
   `python3 infrastructure/scripts/generation/generate_api_dtos.py`; never edit
   generated DTO records manually.
3. Update the owning module controller mapping/bindings and run
   `python3 infrastructure/scripts/quality/audit_controller_contract.py`.
4. Regenerate `API_ENDPOINTS.md` with
   `python3 infrastructure/scripts/generation/generate_api_reference.py`.
5. Update services, mappers/repositories, authorization, frontend API modules and
   stateful/contract-wide tests, then run `make validate` for cross-cutting changes.
