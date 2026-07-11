# Release 0.18.0 — Build Designer command deck

Release 0.18.0 redesigns the Build Designer's live stat area as an operational command deck.
The selected ship, effective core stats, six upgrade slots and combined positive/negative effects
are presented in a single responsive panel on both the editor and the saved-build detail page.

## Stat calculation

The frontend continues to consume backend-provided stat definitions and applies the same base,
percentage and flat-effect rules used by saved builds. Specialist effects now scale with the
selected quantity in both the live preview and backend persistence, eliminating a discrepancy
between the editor and saved detail view.

## Crew capacity

Crew allocation is capacity-aware. Each range input computes its maximum from the selected ship's
effective crew capacity minus the other current allocations. If an upgrade or specialist that adds
crew capacity is removed, the allocation is normalized automatically: optional crew is reduced
first, while sailors are preserved down to the effective minimum.

## Deployment

This release contains no migration and no seed change. Use a normal database-safe update:

```bash
sudo ./update.sh
```
