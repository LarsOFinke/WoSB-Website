# UI/UX Release 0.14

## Build Designer

- Weapon sections with zero ship capacity are omitted.
- Weapon options are filtered by their dedicated bow/stern, broadside or mortar slot metadata.
- A weapon already selected in another row of the same arc disappears from that row's remaining choices.
- An upgrade selected in one upgrade slot disappears from every other upgrade selector.
- Duplicate upgrades are rejected by the API independently of the frontend.

## New Captain Guide

The authenticated `/new-captain` route provides an ordered onboarding roadmap. Administrators and
moderators can edit the introduction, add free-text sections and maintain ordered resource groups
with references to guides, builds, internal routes and external links. The Fleet Portal links the
roadmap as the first item in the New Captain Path.
