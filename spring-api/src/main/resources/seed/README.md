# JSON Master Data

This directory is the sole source for repository-owned master data.
The Java application validates and synchronizes these files idempotently.
The first administrator account is created exclusively from the runtime environment;
installation-specific data does not belong in the catalog.

## Structure

```text
seeds/
├── manifest.json
├── references.json
├── system/
│   ├── roles.json
│   └── fleets.json
├── builds/
│   ├── categories.json
│   └── options/
│       ├── sails.json
│       ├── upgrades.json
│       ├── lanterns.json
│       ├── ammunition.json
│       ├── consumables.json
│       ├── hold.json
│       ├── weapons.json
│       └── specialists.json
└── ships/
    ├── definitions.json
    └── rates/
        ├── rate-1.json
        └── … rate-7.json
```

`manifest.json` lists every JSON document with its type. Unlisted, missing, or duplicate files abort loading. This prevents a new file from silently sitting beside the catalog that is actually loaded.

Every document has `schema_version` and `catalog`. Unknown fields, invalid types, duplicate IDs, and contradictory references are rejected before the first database change.

## Maintenance Rules

- `seed_id` is the permanent technical identity. Renaming changes only `name`, never `seed_id`.
- Every Build option belongs in exactly one file under `builds/options`.
- Renamed upgrade labels are migrated through `aliases` in `upgrades.json` so existing Builds remain connected.
- New ships are added to the file for their rate.
- New JSON files are additionally registered in the manifest.
- Secrets and installation-specific values do not belong in this catalog. The initial administrator account continues to come from the environment.
- Production runs remain idempotent: unchanged records are not rewritten, admin overrides stay protected, and removed defaults are disabled rather than deleted.

## Ships and Weapon Mounts

`ships/definitions.json` contains normalized weapon classes and slot types.
Every ship defines exactly six mounts even when their `capacity` is null:

- `weapon_front`: bow weapons
- `weapon_rear`: stern weapons
- `weapon_port`: port broadside
- `weapon_starboard`: starboard broadside
- `weapon_mortar`: mortars and barrel launchers
- `weapon_special`: optional dedicated special-weapon mount

`special_weapon_capacity` is an upper bound within normal `capacity`. Special weapons are allowed only at the bow, stern, or a dedicated special mount. An equipable mortar mount additionally requires `max_caliber_inches`.

Regular broadside **and** bow/stern weapons have a normalized `weapon_class` (`light`, `medium`, `heavy`). Selection requires both the slot type and the maximum weapon class of the concrete mount to match. Mortars and true special weapons continue to use their separate rules.

`mortar_modification` represents the permanent ship conversion and is not a normal upgrade. `null` means the conversion is unavailable. It is currently defined for `Black Wind`, `Falmouth`, and `Friede`. A Build stores only the selection; capacities and stat effects always come from the ship catalog.

## Execution

The application idempotently synchronizes validated master data at startup after a successful Flyway migration. Administrative overrides remain intact. Deliberate restoration of repository defaults is performed through protected master-data administration and is audited.

No sample Builds, guides, appointments, or user activity are generated.
