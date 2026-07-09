# Project Inventory

This document records the current state of the Iron Crown Fleet Hub after the production-foundation pass. It is intended as the first stop for future maintainers before changing architecture.

## Product scope

The application is a fleet/community hub for World of Sea Battle. It currently covers:

- Build Manager with ship/build option catalog, user-owned builds and guide references.
- Guides with inline file embeds and inline build embeds.
- Forum with inline file embeds.
- Gruppensuche for temporary fleet activities.
- Fleet calendar for staff-created events.
- Fleet management with official membership applications, fleet-specific leadership roles and primary fleet profile synchronization.
- Staff panel for moderation, content review, calendar management and operational shortcuts.
- Localized frontend for EN, DE, FR, ES, PT, RU and CN.

## Backend inventory

| Area | Main files | Responsibility |
| --- | --- | --- |
| App factory | `backend/src/app/__init__.py` | FastAPI construction, middleware, error handlers, static uploads, router registration |
| Config | `backend/src/app/core/config.py` | Environment-backed settings |
| Logging | `backend/src/app/core/logging.py`, `backend/src/app/core/middleware.py` | Central log config, request IDs, duration/status logging |
| Auth/session | `core/security.py`, `services/auth_service.py`, `models/user.py`, `models/auth_session.py` | Password hashing, cookie sessions, roles |
| Profiles | `models/user_profile.py`, `services/profile_service.py` | Public profile data and primary fleet pointer |
| Fleets | `models/fleet.py`, `services/fleet_service.py`, `api/routes/fleets.py` | Fleet catalog, membership applications, fleet leadership |
| Builds | `models/build*.py`, `services/build_service.py` | Build persistence and validation |
| Build options | `models/build_option.py`, `services/build_option_service.py`, `db/seeds/*` | Normalized option catalog and stat effects |
| Guides | `models/guide.py`, `services/guide_service.py` | Guide CRUD, attachments, build references |
| Forum | `models/forum.py`, `services/forum_service.py` | Threads, posts, attachments |
| Files | `models/file_asset.py`, `services/file_service.py` | Upload validation, storage metadata, deletion |
| Calendar | `models/fleet_event.py`, `services/fleet_event_service.py` | Fleet events and staff CRUD |
| Gruppensuche | `models/group.py`, `services/group_service.py` | Group search listings and ownership |
| Seeds | `backend/src/app/db/seeds/*` | Deterministic demo/catalog data |

## Frontend inventory

| Area | Main files | Responsibility |
| --- | --- | --- |
| App shell | `App.vue`, `core/components/AppNavbar.vue`, `AppTopbar.vue`, `AppSidebar.vue` | Topbar/sidebar layout and responsive navigation |
| App shell state | `core/composables/useAppShell.js` | Sidebar collapse/open state and body classes |
| Navigation model | `core/navigation/workspaceLinks.js` | Single source for left navigation ordering |
| Localization | `locales/*`, `scripts/check-locales.mjs` | Runtime translations and strict coverage checks |
| API services | `services/*.js` | Thin HTTP adapters grouped by feature |
| Rendering | `RichTextRenderer.vue`, `AttachmentGallery.vue`, `LinkedBuildList.vue` | Inline media/build rendering |
| Feature pages | `pages/**/*Page.vue` | Route-level screens |
| Styles | `styles/main.css` | Current tokenized design system and responsive rules |

## Data model inventory

The schema is centered around normalized entities:

- `users` stores authentication and global role state only.
- `user_profiles` stores mutable public profile data and the primary fleet membership pointer.
- `fleets` and `fleet_memberships` hold official fleet membership state.
- `ships`, `build_item_categories`, `build_item_options`, `build_item_effects`, `builds` and `build_slots` separate catalog data from user-created builds.
- `guides`, `guide_attachments` and `guide_build_references` separate content, file references and build references.
- `forum_threads`, `forum_posts` and `forum_post_attachments` separate threads, post bodies and uploaded files.
- `stored_files` stores file metadata while the binary file stays in `storage/uploads`.

## Known intentional prototype constraints

- SQLite is supported as the development/demo database. Production should use PostgreSQL and a migration tool before real users.
- Sessions are database-backed cookie sessions. This is simple and adequate for the prototype, but production should review rotation, device management and rate limiting.
- File storage is local disk. Production should move uploads to object storage or a shared volume.
- Rich text embeds use token syntax (`[[file:id|size]]`, `[[build:id|layout]]`). This is deliberate KISS: it can later be replaced by a richer editor while keeping backend validation rules.


## Single Fleet Refactor

Der Flottenbereich arbeitet jetzt mit genau einer offiziellen Iron Crown Fleet. Registrierung, Profil und Flottenverwaltung referenzieren dieselbe zentrale Membership. Details stehen in `docs/SINGLE_FLEET_REFACTOR.md`.
