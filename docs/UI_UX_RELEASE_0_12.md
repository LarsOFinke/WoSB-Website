# RBF UI/UX release 0.12

## Identity refactor

- Renamed the product, fleet seed, deployment defaults and public domain to **Royal Blackwater Fleet [RBF]**.
- Simplified the responsive lockup to “Royal Blackwater” + “Fleet”, retaining the compact RBF monogram.
- Added compatibility paths for previous RBV environment variables, CLI commands, local-storage keys,
  fleet slugs, Compose project names and systemd units.

## Newcomer-first portal

- Reframed the public fleet portal around a four-step path: learn, prepare, ask and participate.
- Made the public Build Library the primary starting point while visibly advertising member Guides,
  Forum Q&A, Calendar and Group Search before login.
- Added a dedicated operations card with the main activity window (12:00–02:00 CET), Port Battle
  focus (18:00–23:00 CET), calendar expectations and Discord communication policy.
- Documented that Discord voice is mandatory for Port Battles and competitive operations, while it
  remains optional but encouraged for normal activity.

## Localization pass

- Moved public portal standard content away from backend seed prose into frontend locale keys.
- Added explicit English, German, French, Spanish, Portuguese, Russian and Simplified Chinese copy
  for the fleet identity, onboarding path, module descriptions, activity schedule and voice policy.
- Added localized application placeholders and access labels.
- Locale validation rejects missing keys, English fallbacks and pseudo-localized strings.

## Responsive design

- Added responsive newcomer cards, a clearer learning-module grid and a compact operations panel.
- Preserved keyboard focus, reduced-motion behavior and mobile navigation from the previous design pass.
- The public portal collapses from four onboarding columns to two and then one without losing order
  or context.
