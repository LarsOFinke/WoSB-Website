# Build-option icon catalog

The Build Designer uses versioned, repository-owned assets under
`frontend/public/build-assets/options/`. Seed records reference these assets via
`image_url`; builds continue to store only option references and never copy an
icon or calculated value.

## Sources

- **32 ship upgrades:** direct crops from the owned-ship upgrade screenshots in
  `docs/ingame-screenshots/ships/`. The ordinary categories use the De Zeven
  Provincien panels; mortar upgrades use the Adventure panel.
- **51 specialists:** direct portrait crops from the four roster screenshots in
  `docs/ingame-screenshots/specialists/`.
- **Sails and lanterns:** small SVG redraws using the shapes, dark framing and
  gold-accent visual language shown in the supplied inventory screenshots. The
  source material does not expose every seeded sail as an isolated bitmap, so
  these assets intentionally avoid pretending to be exact game-file exports.
- **Large and Small Additional Sails:** SVG redraws based on the supplied sail
  inventory screenshot.

The assets are presentation data only. Gameplay effects remain normalized in
seed JSON and are displayed next to each option in the icon-aware picker.

## UI contract

`BuildOptionPicker.vue` provides:

- image, localized label and complete effect summary for every option;
- grouped upgrade categories;
- disabled duplicate specialists;
- keyboard navigation, Escape handling and outside-click closing;
- a mobile bottom-sheet layout that does not overflow the viewport.

Adding a new screenshot-backed option requires both an `image_url` in its seed
record and a committed public asset. Backend and frontend tests enforce this
contract.
