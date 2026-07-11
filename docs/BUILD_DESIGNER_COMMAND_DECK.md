# Build Designer command deck

The command deck is a reusable frontend component at
`frontend/src/modules/builds/components/BuildStatCommandDeck.vue`.

It receives already calculated stat rows and renders four operational layers:

1. selected ship and tactical silhouette;
2. effective core statistics with base and modifier context;
3. a six-slot upgrade rack;
4. combined buffs and debuffs from upgrades and Specialists.

The component is used by both `BuildCreatePage.vue` and `BuildDetailPage.vue`, keeping the live
preview and persisted Build presentation visually consistent.

Crew allocation logic lives in `frontend/src/modules/builds/crewAllocation.js`. It is framework
independent and regression-tested through `frontend/scripts/test-build-designer-inventory.mjs`.
The backend remains authoritative and rejects payloads whose crew total exceeds the effective ship
capacity or whose sailor count falls below the effective minimum.
