# Royal Blackwater Fleet 0.13 — Spring cleanup

This release focuses on production reliability and day-to-day operations.

## Fixed

- Forum replies no longer write a null activity timestamp and therefore no
  longer fail with HTTP 500.
- Seeded guide/forum media is written into the same persistent upload volume as
  the API, fixing `line-battle.svg` and `trade-convoy.svg` 404 responses.
- Exception tracebacks are now persisted correctly and are visible to staff in
  the online log view.
- The top navigation now contains personal shortcuts, while the left sidebar
  remains the module navigation.
- The monitoring action always uses the TLS-only `https://...:8443` URL.

## Added

- Dedicated `update.sh` for normal releases.
- Root-owned systemd path/service update runner triggered by a constrained
  request file rather than Docker socket or shell access from the API.
- **Update Server** control, update state and update transcript in the Staff
  Panel system status.
- Log access and manual refresh for staff roles.
- Regression tests for forum replies, persisted exception logs, upload serving
  and update permissions.
