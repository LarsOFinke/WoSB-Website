# Backend Module Structure

The backend is organized around explicit infrastructure layers plus domain modules. The goal is to keep the project easy to extend without returning to large global `models`, `schemas` or `services` folders.

```text
backend/
├── config/              non-secret repository configuration
├── storage/             repository demo uploads; runtime path is configured by UPLOAD_DIR
└── src/app/
    ├── api/             API router composition and infrastructure endpoints
    ├── cli/             command-line entry points
    ├── core/            config, security, logging, middleware, errors, constants
    ├── db/              SQLAlchemy engine/session and schema lifecycle
    ├── seeds/           deterministic catalog/demo seed data
    └── modules/
        ├── registry.py  explicit SQLAlchemy model registry
        ├── accounts/    auth, registration approval, profiles, sessions
        ├── admin/       admin dashboard, access review, DB log views
        ├── builds/      build designer, catalog options, stat calculation
        ├── calendar/    fleet calendar events
        ├── content/     shared inline embed parsing/rendering helpers
        ├── files/       upload validation and stored file metadata
        ├── fleet/       single official fleet, memberships, directory
        ├── forum/       threads, posts, forum attachments
        ├── groups/      Gruppensuche listings and signups
        ├── guides/      guides, guide attachments, build references
        └── ships/       ship catalog endpoints and schemas
```

## Domain module shape

Each feature module uses the same inner layout when that layer is needed:

```text
modules/<domain>/
├── models/      SQLAlchemy classes and persistence constants
├── routes/      FastAPI router implementation in router.py
├── schemas/     Pydantic request/response contracts
└── services/    business logic and validation
```

`routes/__init__.py` only re-exports `router`. Route implementation belongs in `routes/router.py` or smaller route files if the module grows.

## Rules for new code

1. Put feature code in `app/modules/<domain>`.
2. Keep each concrete class in its own file.
3. Put HTTP handlers in `routes`, request/response contracts in `schemas`, persistence classes in `models`, and business logic in `services`.
4. Keep `api/router.py` as the composition layer only.
5. Keep `db` free of domain logic. It owns engine/session setup and schema lifecycle only.
6. Keep `seeds` deterministic and importable without HTTP dependencies.
7. Put repeated enum-like schema constants in a module-level `schemas/constants.py` file rather than duplicating them per schema.
8. Runtime uploads must be configured through `UPLOAD_DIR`. The repository-local storage tree is only `backend/storage/uploads/demo` for demo assets.

## Import style

Prefer direct module imports for backend code:

```python
from app.modules.builds.services.build_service import create_build
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.guides.schemas.guide_create import GuideCreate
```

Avoid introducing new global aggregate packages. There are intentionally no root-level `app/models`, `app/schemas` or `app/services` directories.
