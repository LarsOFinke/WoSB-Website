# Architecture Notes

Blackwater Mercenaries Hub uses matching feature boundaries in FastAPI and Vue. A domain owns its persistence/contracts/business logic on the backend and its routes/screens/API adapter on the frontend.

## Backend layering

```text
src/app/
├── api/                  router composition and infrastructure endpoints
├── core/                 config, auth dependencies, logging and errors
├── db/                   SQLAlchemy engine/session and schema lifecycle
├── seeds/                deterministic seed data
└── modules/<domain>/
    ├── models/            SQLAlchemy persistence classes
    ├── schemas/           Pydantic contracts
    ├── services/          business rules and persistence workflows
    └── routes/            HTTP handlers and dependency boundaries
```

Keep route handlers thin. A route declares access, parses HTTP input and translates service errors; business rules stay in services.

## Frontend layering

```text
src/
├── core/                 app shell, navigation and reusable workspace UI
├── shared/               cross-domain API/query/content utilities
├── modules/<domain>/
│   ├── api/              thin endpoint adapters
│   ├── pages/            route-level screens
│   └── routes.js         lazy routes and access metadata
├── router/               route composition and global session guards
├── locales/              runtime i18n and message layers
└── styles/               shared design tokens and workspace sections
```

Do not recreate global `pages/` or `services/` directories. New frontend code belongs to the module that owns the backend domain. Reuse the shared workspace header, metric cards, panels, forms and buttons before adding local CSS.

## Access model

Public product surfaces are intentionally narrow: fleet portal/home, login, registration and build catalog/details. Profile, guides, groups, forum, calendar, fleet management, personal workspaces and content creation require login. Staff operations require moderator/admin permissions where appropriate.

Vue route guards provide redirects and navigation visibility. FastAPI dependencies remain the security source of truth.

## Roles and permissions

Global website roles:

- `user`
- `moderator`
- `admin`

Fleet roles are scoped per fleet membership, not global account state:

- `member`
- `fleet_lieutenant`
- `fleet_admiral`

Staff features check the global role; fleet management checks active fleet leadership membership or admin status.

## Locales

English remains the canonical fallback layer. Every supported locale receives the English base first and then locale-specific overrides.

```text
de, en, fr, es, pt, ru, cn
```

## Demo content

Fresh seeds include guides and forum threads with local demo media. They use the same stored-file and attachment model as real uploads, while their routes remain protected by the normal authenticated access policy.
