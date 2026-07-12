# Build Designer catalog audit (2026-07-12)

The Build Designer master data has been reconciled against the supplied in-game panels and event tooltips. Player-state messages, owned resources, unlock progress, construction prices and port restrictions are intentionally excluded.

## Completion batch

The final five previously wiki-audited records were verified against the newly supplied current in-game panels:

- **La Creole**: regular weapon class corrected to `light`; orientation corrected to `4-12-0`.
- **Black Wind**: regular weapon class corrected to `light`; layout confirmed as `2-16-2`. The generic `Mortar modification available` notice is not treated as a quantified mortar mount.
- **Russia**: regular weapon class corrected to `light`; orientation corrected to `2-14-0`.
- **San Martin**: regular weapon class corrected to `light`; layout confirmed as `0-20-0`.
- **Le Requin**: regular weapon class corrected to `light`; orientation corrected to `2-12-0`, with one mortar mount up to 7 inches.

The ship catalog contains **67 active seed records**. All **67** are now backed by supplied in-game screenshots or current-event tooltips. A regression test enforces that no active ship seed falls back to wiki-only provenance.

## Earlier final additions

- **De Zeven Provincien**: current in-game panel; standard five upgrade slots because the panel does not show `Spaces for upgrades +1`.
- **Sovereign**: current in-game panel; weapon orientation `4-38-8 + mortar 7in x2`; standard five upgrade slots.
- **Leopard**: current-event rate III Ship of the Line with medium mounts and layout `0-25-4`.
- **Ice Lantern**: current-event lantern with `+5% speed`, `+5% hold capacity` and `+5% durability`.

## Fields represented by the Build Designer

- name, rate and ship type
- durability, speed, maneuverability and broadside armor
- hold and crew capacity
- editable planning sailor minimum
- displacement
- sail, lantern and upgrade-slot availability
- maximum regular weapon class
- bow, side and stern weapon capacities
- mortar capacity/caliber and special-weapon capacity

## Intentionally excluded

- green inventory or upgrade notices
- player resources, construction costs and owned currencies
- unlock, event and experience progress
- port/faction restrictions and build availability messages
- hull dimensions, swivel guns and integrity
- historical descriptions and role labels
- unique wind rose, oars, named passives, XP/loot bonuses and Imperial NPC behavior
- unquantified notices such as `Mortar modification available`

Those values are either player state, presentation-only data, or outside the current Build Designer calculation model.

## Planning metadata

The supplied ship panels do not expose minimum sailing crew. `sailor_minimum` therefore remains a documented planning value. The shared seed factory derives 40% of crew capacity unless an explicit project value is retained. Administrators can correct this field later in the master-data panel without losing the override on subsequent seed runs.
