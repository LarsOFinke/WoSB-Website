# Spring cleanup — Release 0.17.0

The cleanup pass removes transitional data and code left by the prototype releases while preserving user-created content.

## Removed from deployment seeds

- generic demo Builds;
- fake forum discussions;
- generated fleet events;
- example group-search listings;
- demo SVG uploads and attachment records.

Fresh installations receive only required catalogs, the official fleet, the administrator account, curated progression templates/guides and the New Captain roadmap.

Upgraded installations remove historic sample records only while their original seed marker still matches. Staff-edited guides or renamed/rewritten content are kept.

## Authorization cleanup

- role strings moved to normalized role catalogs;
- authority checks use ranks/capabilities rather than scattered string comparisons;
- moderators cannot deactivate, demote or otherwise modify administrators;
- peer administrators cannot take over one another through the dashboard;
- Fleet Admiral and Fleet Lieutenant leadership is derived from active normalized memberships.

## Data cleanup

- registration and fleet application data are separate;
- the duplicate profile-to-primary-membership pointer is removed;
- preferred ships are child rows rather than comma-separated storage;
- ship weapon layouts and option slot lists are normalized;
- obsolete derived weapon eligibility rows are not persisted.

## Validation

The release validator covers backend permissions, fresh and upgraded migrations, production seeding, weapon eligibility, frontend inventory behavior, locale completeness, Vite production build, Compose syntax and first-run simulation.
