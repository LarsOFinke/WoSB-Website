# Uptime Kuma 1 → 2 migration runbook

The production Compose file intentionally remains on `louislam/uptime-kuma:1.23.16` until this
runbook is executed in a planned maintenance window. Version 2 performs a potentially long database
migration and must not be introduced as an unattended application update.

## Preconditions

1. Confirm adequate free disk space on the host.
2. Stop writes to the monitoring instance.
3. Stop the monitoring services:

   ```bash
   cd infrastructure
   docker compose --env-file .env -f compose.yml --profile monitoring stop \
     monitoring-gateway uptime-kuma
   ```

4. Create two independent copies of `infrastructure/data/uptime-kuma`; keep one off-host.
5. Verify both archives can be listed and their SHA-256 checksums match the recorded values.

## Staged migration

1. Change only the Uptime Kuma image to the reviewed current 2.x patch release.
2. Start Uptime Kuma without the monitoring gateway:

   ```bash
   docker compose --env-file .env -f compose.yml --profile monitoring up -d uptime-kuma
   docker compose --env-file .env -f compose.yml logs -f uptime-kuma
   ```

3. Do not interrupt the database migration. On Raspberry Pi hardware it may take substantially
   longer than on a desktop system.
4. After the container reports ready, verify login, all monitors, notification targets, status pages
   and historical heartbeat data.
5. Start `monitoring-gateway`, run the repository smoke test and observe the service for at least one
   complete monitor interval.

## Rollback

Do not reuse a partially migrated data directory. Stop the new container, remove or quarantine the
migrated directory, restore the verified v1 data copy and restore the original `1.23.16` image tag.
Then start the old service and verify all monitors before ending the maintenance window.
