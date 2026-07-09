# Architecture Notes

The project is still a prototype, but the current structure is intentionally shaped so new modules can be added without turning the codebase into a single feature blob.

## Backend layering

```text
api/routes/   HTTP concerns: auth dependencies, status codes, request/response schemas
schemas/      Pydantic DTOs and input validation
services/     Business rules and persistence workflows
models/       SQLAlchemy tables and relationships
db/seeds/     Idempotent seed data grouped by domain
```

Keep route handlers thin. A route may check access and translate service errors to HTTP errors, but business rules should live in services.

## Frontend layering

```text
pages/        Route-level views and feature composition
core/         Shared shell and reusable components
services/     API calls and session state
locales/      Runtime i18n API plus feature/domain message layers
styles/       Shared design tokens and module sections
```

New feature pages should reuse the shared card, filter, form and button classes before adding local CSS.

## Roles and permissions

Global website roles:

- `user`
- `moderator`
- `admin`

Fleet roles are scoped per fleet membership, not global user account state:

- `member`
- `fleet_lieutenant`
- `fleet_admiral`

This keeps authorization simple: staff features check the global role; fleet management checks active fleet leadership membership or admin status.

## Locales

English remains the canonical fallback layer. Every supported locale receives the English base first and then locale-specific overrides. This guarantees complete key coverage while allowing the individual locale files to grow module by module.

Supported locales:

```text
de, en, fr, es, pt, ru, cn
```

## Demo content

Fresh seeds now include two guides and two forum threads with local SVG demo images. The images are stored through the same `stored_files` / attachment model used by real uploads, so the Forum and Guide embeds exercise the same code path as user content.
