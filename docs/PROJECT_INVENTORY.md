# Project inventory — 0.18.0

Royal Blackwater Fleet is a localized fleet/community hub for World of Sea Battle.

## Access boundary

Anonymous visitors can access only the landing page, compact public fleet page and authentication/registration routes. Builds, ships, guides, forum, calendar, groups, squads, the New Captain Guide, profiles and staff/fleet administration require a session.

## Product modules

- Build Designer with ship-specific weapon eligibility, capacity-aware crew controls, an enterprise command deck and official progression templates
- Guides with file and Build references
- Forum and persistent Q&A
- Temporary group searches
- Fleet and squad calendar
- Official fleet membership and leadership management
- Permanent squads with scoped roles and private appointments
- Personal workspaces for Builds, groups and Squads
- Editable New Captain progression roadmap
- Staff dashboard, persistent logs and controlled server updates

## Backend map

| Area | Location | Responsibility |
| --- | --- | --- |
| App/runtime | `backend/src/app/core`, `backend/src/app/api` | FastAPI factory, middleware, health and router assembly |
| Accounts | `backend/src/app/modules/accounts` | login, sessions, registration approval and profiles |
| Permissions | `backend/src/app/modules/permissions` | normalized role catalogs, ranks and capability assignment |
| Admin | `backend/src/app/modules/admin` | account hierarchy, review, logs and update control |
| Fleet | `backend/src/app/modules/fleet` | official fleet, membership applications and leadership |
| Squads | `backend/src/app/modules/squads` | permanent sub-units, scoped roster roles and workspace |
| Calendar | `backend/src/app/modules/calendar` | fleet-wide and squad-scoped events |
| Ships/Builds | `backend/src/app/modules/ships`, `backend/src/app/modules/builds` | catalog, mount compatibility, builds and stat calculation |
| Content | `guides`, `forum`, `files`, `content` modules | authored content, references and uploads |
| Groups | `backend/src/app/modules/groups` | temporary activity listings and signups |
| Onboarding | `backend/src/app/modules/onboarding` | editable New Captain roadmap |
| Migrations | `backend/migrations` | reviewed PostgreSQL/SQLite schema evolution |
| Seeds | `backend/src/app/seeds` | required catalogs, official fleet and curated onboarding content |

## Frontend map

- `frontend/src/core`: shell, auth state, navigation and shared UI
- `frontend/src/modules`: feature pages and API clients
- `frontend/src/locales`: EN, DE, FR, ES, PT, RU and CN dictionaries
- `frontend/scripts`: environment, locale and Build Designer regression checks

The top navigation contains personal workspaces. The left sidebar contains application modules. Fleet Management is visible only to staff or active Fleet Admiral/Fleet Lieutenant memberships.

## Deployment data policy

Runtime state lives below `infrastructure/data/` and is never tracked by Git. Normal `./update.sh` runs rebuild API and gateway without touching PostgreSQL. Schema/catalog releases explicitly use migration/seed flags. No update command runs a database reset or removes the PostgreSQL volume.
