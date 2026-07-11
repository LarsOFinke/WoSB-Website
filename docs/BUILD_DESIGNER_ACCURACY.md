# Build Designer catalog and weapon eligibility

Release 0.17.0 replaced the old rate/pound heuristics and serialized slot metadata with normalized, ship-specific mount rules.

## Source-of-truth model

Each ship has one row per mount arc in `ship_weapon_mounts`:

- bow
- stern
- port broadside
- starboard broadside
- mortar

A mount stores capacity and either a maximum Light/Medium/Heavy weapon class or, for mortars, a maximum caliber. Each weapon option stores its own class and allowed slot types through normalized foreign keys and a join table.

Eligibility is derived at request and validation time:

```text
selected ship mount exists
+ mount capacity > 0
+ weapon supports that arc
+ weapon class <= mount class
+ mortar caliber <= mortar ceiling
= selectable weapon
```

The frontend requests `/api/builds/options?ship_id=<id>` whenever the ship changes. The backend also validates the same rules when saving, so a crafted request cannot bypass the dropdown filtering.

## Catalog behavior

- zero-capacity arcs are omitted from the editor;
- broadside cannons/carronades never appear in bow or stern selectors;
- bow/stern weapons never leak into broadside selectors;
- mortars appear only on ships with a mortar mount and compatible caliber;
- already-selected upgrades disappear from remaining upgrade selectors;
- inactive legacy options stay attached to historic builds but are unavailable for new selections.

Every active regular weapon is required to have a normalized class and every seeded ship has an explicit maximum class. Seed validation fails loudly on duplicate names, unknown slots/classes, invalid layouts or missing source metadata.

## Accuracy policy

The repository catalog is a maintained planning dataset, not an official game API export. Source metadata and regression tests make corrections reviewable. A later catalog correction should update the seed rows and tests; the schema and compatibility algorithm do not need to be redesigned.


## 0.18.0 live-stat and crew consistency

The command deck uses the backend stat-definition contract for its labels, units, precision and
modifier semantics. Specialist quantities multiply their effects in both the editor and persisted
Build calculation. Crew range inputs cannot allocate more than the effective capacity remaining
after all other crew groups, and server-side validation remains authoritative.
