# Documentation Index

Start here when onboarding or planning the next production-grade iteration.

## Foundation documents

- [Project Inventory](PROJECT_INVENTORY.md)
- [Rebuild Plan](REBUILD_PLAN.md)
- [Backend Architecture](BACKEND_ARCHITECTURE.md)
- [Frontend Architecture](FRONTEND_ARCHITECTURE.md)
- [Operations](OPERATIONS.md)
- [Production Checklist](PRODUCTION_CHECKLIST.md)

## Feature documents

- [Database Schema](DATABASE_SCHEMA.md)
- [Localization](LOCALIZATION.md)
- [Inline Media Embeds](INLINE_MEDIA_EMBEDS.md)
- [Guide Build Embeds](GUIDE_BUILD_EMBEDS.md)
- [App Shell UI](APP_SHELL_UI.md)
- [UI/UX Notes](UI_UX_NOTES.md)
- [Architecture](ARCHITECTURE.md)

Feature documents are kept because they describe working prototype behavior. The foundation documents above are the current source for production-readiness decisions.


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.


## Single Fleet Refactor

Der Flottenbereich arbeitet jetzt mit genau einer offiziellen Iron Crown Fleet. Registrierung, Profil und Flottenverwaltung referenzieren dieselbe zentrale Membership. Details stehen in `docs/SINGLE_FLEET_REFACTOR.md`.

- [Build Designer Accuracy](BUILD_DESIGNER_ACCURACY.md)
- [Build Designer: Waffenvalidierung & Special Crew](BUILD_DESIGNER_WEAPONS_AND_CREW.md)

- `FLEET_HOME_GROUP_SIGNUPS_LOGGING.md` — fleet portal home route, group signup workflow and DB logging policy.
