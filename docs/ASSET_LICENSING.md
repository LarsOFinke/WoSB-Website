# Asset licensing and release boundary

This repository contains two intentionally separate frontend asset families.
The default public build uses only the first one.

| Material | Location | Permission status |
| --- | --- | --- |
| Project-owned code, documentation, and neutral redraws | Repository files and `frontend/public/build-assets/neutral/` | AGPL-3.0-or-later, unless a file says otherwise |
| In-game screenshots used as research evidence | `docs/ingame-screenshots/` | No project license; retained for private/reference use only |
| Crops derived from in-game screenshots | `frontend/game-assets/` | No project license; publication is disabled by policy pending written permission |

The screenshots, game-derived crops, game names, logos, characters, visual
designs, and other material originating with the game or its publisher remain
subject to their respective owners' rights. The fact that a file is present in
this repository does not grant permission to copy, redistribute, publish,
sublicense, or use it commercially. No affiliation or endorsement is implied.

## Build rule

`VITE_BUILD_ASSET_MODE=neutral` is the default and is the only approved mode
for public, test, and production deployments while written permission is
pending. It excludes game-derived files from the generated frontend and maps
game asset references to neutral placeholders.

The `game` mode exists only as a development and authorization switch. It must
not be enabled in a release, deployment artifact, screenshot, demo, or hosted
environment until the project has recorded written permission from the
relevant rights holder. When permission is obtained, record its scope,
territory, duration, attribution requirements, and covered files in a separate
non-secret project record before enabling the mode.

This boundary also applies to the source screenshots: they must not be copied
into `frontend/public/`, a release archive, a Docker image, or a hosted static
asset directory.

For the current asset mapping and neutral replacements, see
[`BUILD_OPTION_ICONS.md`](BUILD_OPTION_ICONS.md) and
[`ingame-screenshots/README.md`](ingame-screenshots/README.md).
