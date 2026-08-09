# Build-option icon catalog

The Build Designer uses versioned, repository-owned assets under
`frontend/public/build-assets/neutral/` and an inactive, authorization-gated
game-derived source tree `frontend/game-assets/`. Seed records reference these assets via
`image_url`; builds continue to store only option references and never copy an
icon or calculated value.

## Asset modes

The frontend reads `VITE_BUILD_ASSET_MODE` and accepts `neutral` or `game`.
`neutral` is the default and is the only approved mode for public deployments
while permission to publish game-derived imagery is pending. It uses the neutral
SVG catalog and category visuals for specialists and upgrades. `game` is an
explicit opt-in reserved for a documented authorization; Vite emits the game
source tree only for that mode. It must not be used in hosted or release builds
before that authorization exists. The central
`buildOptionVisual` resolver prevents game paths from being rendered in neutral
mode.

## Sources

- **32 ship upgrades (game mode):** direct crops from the owned-ship upgrade screenshots in
  `docs/ingame-screenshots/ships/`. The ordinary categories use the De Zeven
  Provincien panels; mortar upgrades use the Adventure panel.
- **51 specialists (game mode):** direct portrait crops from the four roster screenshots in
  `docs/ingame-screenshots/specialists/`.
- **Sails and lanterns:** small SVG redraws using the shapes, dark framing and
  gold-accent visual language shown in the supplied inventory screenshots. The
  source material does not expose every seeded sail as an isolated bitmap, so
  these assets intentionally avoid pretending to be exact game-file exports.
- **Large and Small Additional Sails:** SVG redraws based on the supplied sail
  inventory screenshot.

The game-derived assets are not covered by the repository license. The assets
are presentation data only. Gameplay effects remain normalized in
seed JSON and are displayed next to each option in the icon-aware picker.

## UI contract

`BuildOptionPicker.vue` provides:

- image, localized label and complete effect summary for every option;
- grouped upgrade categories;
- disabled duplicate specialists;
- keyboard navigation, Escape handling and outside-click closing;
- a mobile bottom-sheet layout that does not overflow the viewport.

Adding a new game-derived option requires an `image_url` under the `game`
asset tree and a committed public asset. Neutral-mode options must resolve to a
neutral category visual. Backend and frontend tests enforce this contract.
