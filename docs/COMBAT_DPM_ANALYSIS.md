# Combat DPM analysis

The member-only `/combat-analysis` module compares sustained standard-weapon damage for four firing categories:

- one broadside;
- both broadsides while side-switching;
- bow;
- stern.

Each category has an independent target-armor input. The configured broadside is stored once in the page state; the side-switching result deliberately doubles its weapon quantities instead of maintaining a second, potentially divergent loadout.

## Calculation contract

For every selected weapon profile:

```text
modified_damage = base_damage × damage multipliers
modified_reload = base_reload ÷ reload-speed multipliers
armor_damage = max(0, modified_damage − target_armor)
DPM = armor_damage × 60 ÷ modified_reload × quantity
```

Independent option effects are stacked with the same multiplicative percentage contract used by the Build Planner. The module currently includes sustained standard-weapon effects for general damage, standard reload speed, bow/stern damage, low-hull damage and the verified low-durability reload-per-Sailor Specialist effect. Single-shot, ammunition-switch, mortar, swivel-gun and item-reload effects are intentionally outside this calculation.

## Normalized data model

Weapon performance is not embedded in page code, ship rows or saved Builds. Table `weapon_performance_profiles` stores exactly one optional performance profile per `build_item_options` weapon row:

- `option_id` — primary and foreign key;
- `base_damage`;
- `reload_seconds`.

Target armor and selected modifiers are calculation inputs and are therefore not persisted in that table. Weapon compatibility continues to come from normalized slot types and Light/Medium/Heavy mount ceilings.

The Staff master-data editor can maintain the performance profile for standard broadside and bow/stern weapon options. Removing a profile makes the analyzer report the weapon as unverified instead of calculating with an estimated value.

## Initial reference data

Migration `0012_weapon_performance_profiles` and the weapon seed catalogue include the 21 broadside cannon damage/reload pairs supplied by the project owner on 2026-07-30. The screenshot-derived formula was checked against its armor columns, including the 6-pdr Rusty Cannon example.

No bow/stern damage or reload values were present in that source. Those profiles are intentionally left empty until verified values are supplied. The analyzer shows a visible missing-data warning and calculates only the verified subtotal; it never invents fallback values.

## Deployment

This feature requires `Update + Migrate` to apply migration `0012`. A separate seed run is not required because the migration backfills existing repository-owned cannon rows, while future clean installations receive the same profiles from the seed catalogue.
