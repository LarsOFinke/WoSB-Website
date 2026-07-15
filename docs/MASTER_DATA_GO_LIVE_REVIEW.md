# Master-data and Build Designer go-live review

Date: 2026-07-12

## Decision

**Ready for a staged production release.** The seed structure, API and Build Designer calculation path are internally consistent, repeatable and protected against accidental overwrite of administrator changes.

The data basis is solid for the current Build Designer scope. All 67 ship records in the supplied catalog are now backed by in-game screenshots or current-event tooltips. An absolute claim that no additional game ship exists still requires an official export or a complete in-game catalog comparison.

Shipyard-panel speed values are normalized from the raw metres-per-second display to knots before they enter the master-data catalog. This keeps base ship speed in the same unit as flat sail and upgrade bonuses.

## Catalog state

| Area | State |
| --- | --- |
| Ships | 67 active seed records |
| Screenshot/event-audited ships | 67 |
| Wiki-only ships | 0 |
| Lanterns | 9, including Ice Lantern |
| Stable seed identity | Present (`seed_key`) |
| Repeatable updates | Checksum/revision based |
| Admin override protection | Present |
| Removed defaults | Deactivated, not destructively deleted |
| Weapon mounts | Normalized tables and slot taxonomy |
| Upgrade slots | API, database and calculator aligned to a maximum of 6 |

## Maintainability

The ship data is grouped by in-game rate instead of living in one monolithic file:

- `app/seeds/ship_data/common.py` contains provenance constants, types and the canonical factory.
- `rate_1.py` through `rate_7.py` contain focused catalog slices.
- shared defaults cover the normal five upgrade slots, one sail slot, lantern availability and the documented crew-planning rule.
- exceptions such as event provenance, special weapons, six-slot ships and explicit sailor targets remain next to the affected record.
- the public import contract (`SHIP_SEED_DATA`) remains unchanged.

Validation rejects invalid rates, negative capacities, sailor targets above crew capacity, invalid weapon classes/layouts, non-boolean lantern capability and upgrade-slot values outside the six-slot model. Regression tests require every active ship seed to be present in the screenshot/event audit map and to carry current panel/event provenance.

## Admin and minimum crew

Minimum sailing crew is not exposed in the supplied game panels. The seed therefore uses a documented planning value, while `sailor_minimum` remains editable in the master-data administration. Seed checksum and override handling preserve an administrator correction across later seed runs until the record is explicitly restored to its seed default.

## Web interface

The master-data page provides a responsive catalog workspace with searchable lists, record-state badges, grouped ship fields, mount summaries, image preview and persistent save controls. The existing API contract and override/restore behavior remain unchanged.

## Frontend bundle

The previous Vite warning for a JavaScript chunk above 500 kB was resolved using Vite 8/Rolldown code-splitting groups:

- application locales are emitted as a dedicated chunk;
- Vue/Vue Router are emitted as a framework vendor chunk;
- Markdown rendering and sanitization dependencies are emitted as a rich-text vendor chunk;
- remaining third-party modules have a vendor fallback group.

In the verified production build, the largest JavaScript chunk is the locale chunk at approximately **459.64 kB**; the application entry is approximately **32.68 kB**. Vite emits no chunk-size warning.

## Verification evidence

- 86 backend tests passed across 26 isolated test modules;
- Ruff reported no Python lint errors;
- 10 frontend unit tests passed;
- Build Designer inventory regressions passed;
- all seven locale catalogs passed with 1,414 keys each and no fallbacks;
- the Vite production build completed without a chunk-size warning;
- Alembic upgraded an empty database to head and reported no pending model operations;
- the squashed `0001_baseline` completed upgrade, check, downgrade and rebuild;
- infrastructure syntax/security checks and repository invariants passed.

## Remaining known gaps

### 1. Minimum sailing crew

Most records use the documented 40% planning rule until administrators enter verified values. The interface must continue to identify this as a planning value rather than an official game statistic.

### 2. Exhaustive game-catalog completeness

The seed is complete relative to the repository's previous catalog plus every supplied screenshot. No official machine-readable game catalog was provided, and future events may introduce additional ships or equipment.

### 3. Images

The schema and admin interface support image references, but artwork is optional and is not required for calculation correctness.

### 4. Event lifecycle

Leopard and Ice Lantern remain active calculation records because acquired event content can be used in saved builds. Acquisition availability should later be modeled separately rather than by deactivating calculation data.

## Release acceptance

Before production promotion:

1. run migrations and the production seed twice; the second run must be idempotent;
2. create a Leopard build with Ice Lantern and verify speed `19.6 kn`, hold `17325`, durability `2142`;
3. edit a seeded ship's minimum crew, run the seed again and confirm the admin override remains;
4. restore the seed default and verify the calculated planning value returns;
5. create, save, reopen and edit a normal build on desktop and mobile-width layouts.
