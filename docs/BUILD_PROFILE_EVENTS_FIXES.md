# Build Designer, Profile and My Squads fixes

This release consolidates the reported production issues around build quantities, crew calculation, profile preferences, date entry and the personal squad workspace.

## Build Designer

- `Sail Handler` and `Doctor` are active specialist catalog entries with stable seed identities.
- `Doctor` adds six crew places. The Anson regression case is covered with 160 base crew and 166 effective crew when one Doctor is selected.
- Total specialist quantity is capped at eight in both the browser and the API.
- Every weapon position is capped by the selected ship's normalized mount capacity. Quantity inputs expose only the remaining capacity and the API rejects manipulated payloads.
- `Tackles` is available in the Hold catalog.
- Armor is displayed as an absolute armor value. Percentage modifiers remain percentages, but the resulting armor value has no `%` unit.
- Owners can edit non-template builds from the build detail page and from My Builds. Creation and editing share the same validation path.
- The sailing-crew denominator is treated as the target for 100% working speed. Existing API payloads above that target remain readable, while the interactive slider stops at the useful target.

## Profile

- Preferred ships and roles use a transfer-list component. Selecting an item moves it from Available to Selected; selecting it on the right removes it again.
- Updating only the profile note reuses existing normalized preference rows instead of inserting duplicate `(profile_id, preference_id)` pairs.
- The profile update remains atomic and keeps ship and role preferences in normalized association tables.

## Date and time fields

- Native date and time values are entered in separate controls.
- The application validates `YYYY-MM-DD` and `HH:MM` independently before creating a local ISO value.
- Invalid concatenated values such as `12.07.202612 23:23` are no longer accepted or produced.
- Calendar events and group-search schedules use the shared date/time component.

## My Squads / Upcoming Events

- My Squads now contains explicit tabs for squad assignments and upcoming squad events.
- The Upcoming Events tab displays every non-cancelled future event belonging to one of the user's assigned squads, sorted by start time.
- Each row shows squad, localized date/time, event type and optional location, with a direct link to the filtered calendar.
- A visible empty state is shown when no upcoming squad event exists.

## Deployment

No database schema migration is introduced by this release. A seed run is required for the renamed specialists and `Tackles` catalog entry:

```bash
sudo ./update.sh --seed
```

For a ZIP deployment:

```bash
sudo ./update.sh --skip-pull --seed
```

The Admin action **Update + Migration + Seed** is also safe to use.

## Verification

- 76 backend tests passed in two complete grouped runs.
- Build editing, Anson + Doctor crew calculation, specialist limits, weapon capacity, profile-note updates and catalog completeness have dedicated regressions.
- Frontend inventory, crew allocation, preference transfer, date parsing and upcoming-event filtering checks passed.
- All seven locale catalogs are complete.
- Vite production build passed.
- Ruff passed for all changed Python files.
