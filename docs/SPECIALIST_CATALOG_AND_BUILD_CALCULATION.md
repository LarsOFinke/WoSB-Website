# Specialist catalog and Build Designer calculation

## Scope

This release replaces the placeholder Specialist catalog with the 42 entries that are readable in the project-owner screenshots dated 2026-07-11. The catalog is grouped in the source as Pirates, Sailors, Military and Adventurers and remains editable through **Admin → Master data**.

## Important correction

`Doctor` does **not** increase ship crew capacity. Its verified effect is:

- Boarding-company survivability during shelling: `+40%`

The Anson therefore remains at its catalog capacity of `160` crew unless another verified ship, upgrade or equipment effect changes that value. A payload with `166` assigned crew is rejected by the API.

`Surgeon` is a separate Military Specialist. Its effect is:

- Half of crew wounded by cannon fire is healed during repairs.

## Direct and conditional effects

Always-on values use the normal stat pipeline. Examples:

- Sail Handler: speed `+4%`
- Gunner: reload speed `+4%`
- Artillerist: mortar aiming speed `+25%`
- Watchman: fire-extinguishing speed `+40%`

Conditional effects keep separate stat keys and are not permanently applied to the ship's base profile. Examples:

- Steersman: maneuverability while durability is at or below 50%
- Armorer: faster next reload after a single cannon shot
- Master Gunner: conditional reload bonus while durability is at or below 50%
- Ship's Carpenter: repairs at second speed

Boolean abilities are displayed as active capabilities rather than numeric ship-base modifiers.

## Crew-dependent effects

The frontend and backend share the same calculation contract for tooltip values that scale with the current crew allocation.

- First Mate: `0.2% × assigned Sailors` is added to speed
- Sub-lieutenant: `0.1% × assigned Sailors` is added to item reload speed
- Commander: `0.2% × assigned Sailors` is added to ammunition-switch speed
- Master Gunner: `0.1% × assigned Sailors` is shown as the low-durability reload bonus
- Skipper and Fisherman scale with assigned boarders
- Boatman scales with assigned Sailors

For this calculator, boarders are Soldiers, Musketeers and Mercenaries combined.

## Capacity rules

The existing hard limits remain active in both browser and API validation:

- maximum 8 Specialists in total
- weapon quantities cannot exceed the selected ship mount capacity
- duplicate item rows are rejected; quantities stack in one row

## Seed behavior

The master-data seed revision is now:

```text
2026-07-master-data-v4-specialists
```

A seed run updates untouched catalog records and deactivates superseded placeholder Specialists. Existing builds remain readable because records are soft-deactivated rather than deleted. Admin-overridden records remain protected; use **Restore seed default** on a Specialist if an older manual override should be replaced by the verified value.

## Deployment

No schema migration is required for this release. The seed run is required:

```bash
sudo ./update.sh --seed
```

For an extracted ZIP:

```bash
sudo ./update.sh --skip-pull --seed
```

The Admin action **Update + Migration + Seed** is also safe to use.
