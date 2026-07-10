# Build Designer Accuracy Pass

This pass turns the Build Designer into a data-driven planning prototype instead
of a mostly form-based slot editor.

## Goals

- Replace placeholder ship seed stats with a complete ship catalog payload.
- Show base ship stats, selected upgrade modifiers, and effective build stats.
- Keep upgrade effects normalized in `build_item_effects` so the UI does not need
  hard-coded business rules.
- Guard the catalog with seed quality checks so placeholder values cannot silently
  re-enter the demo database.

## Data model

The Build Designer now relies on these normalized data sources:

- `ships`: base catalog values such as durability, speed, maneuverability, armor,
  cargo hold, crew, weapon layout and displacement.
- `build_item_options`: visible selectable equipment/upgrade names.
- `build_item_effects`: one row per normalized effect key and value.
- `build_slots`: the selected options inside a concrete build.

The runtime stat table is derived from:

```text
ship base value + selected upgrade effects = effective build value
```

The central stat definitions live in:

```text
backend/src/app/modules/builds/services/build_stat_service.py
```

This keeps the calculation deterministic and shared by API responses and frontend
previews.

## Upgrade slot rules

The prototype now supports six upgrade slots with these rules:

- Slots 1-4 are the normal build slots.
- Slot 5 is unlocked by an expansion effect in slots 1-4.
- Slot 6 is available either through a ship extra slot or a `+2` expansion effect.
- `Structural Expansion` is seeded as `extra_upgrade_slots: 2` and applies the
  documented maneuverability trade-off used by the planner data.

## Quality checks

`backend/src/app/seeds/build_catalog_quality.py` validates the catalog before
seeding. It checks for:

- duplicate ship names
- missing required ship stats
- zero-value prototype stats
- duplicate upgrade names
- empty or malformed upgrade effects

If a seed row fails the check, seeding stops loudly instead of creating a broken
local demo database.

## Accuracy caveat

The current implementation is as accurate as possible for this prototype using
publicly available wiki/planner/community data. It is not an official game API
export. If an official export becomes available, update only the seed catalog and
stat-effect rows; the calculation and UI can remain unchanged.
