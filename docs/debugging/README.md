# Debugging and Incident Runbooks

These runbooks document failure patterns that actually occurred during Spring Boot deployment
and operation of the website server. They are deliberately limited to diagnostics and safe next
steps; no guide copies secrets, cookies, or Authorization headers into tickets.

- [Module-oriented debugging](MODULE_DEBUGGING.md) – layer separation, minimum evidence, and matching regression-test level
- [Deployment incidents](DEPLOYMENT_INCIDENTS.md) – known concrete symptoms, causes, and safe next steps
- [Legacy build data migration](LEGACY_BUILD_DATA_MIGRATION.md) – reviewed build-only Python→Java partial restore with dry run, semantic FK resolution, and test→production promotion

## Quick narrowing

From the origin system, use the interactive redacting collector first:

```bash
./infrastructure/scripts/diagnostics/debug.sh
./infrastructure/scripts/diagnostics/debug.sh --area calendar --category http-500 --since 30m --tail 400
```

Without a flag it uses `.env.origin.test`; production is selected only with `--production`
and `.env.origin.production`. Agent-suitable output is stored locally under `.diagnostics/`
and does not modify the target system. Direct target-server commands are only the manual fallback:

```bash
sudo systemctl status rbf-hub.service --no-pager
sudo journalctl -u rbf-hub.service -n 200 --no-pager
sudo /srv/rbf/current/infrastructure/scripts/services/status.sh
sudo /srv/rbf/current/infrastructure/scripts/checks/doctor.sh
sudo /srv/rbf/current/infrastructure/scripts/services/logs.sh api gateway
```

For a failed release, first preserve the activation diagnostics under
`/srv/rbf/shared/deployments/failed-*.log`. Clean up containers and networks only afterward;
the diagnostics must not be lost through `docker compose down`.

The detailed collection is in [`DEPLOYMENT_INCIDENTS.md`](DEPLOYMENT_INCIDENTS.md).

## Build image preparation fails after one successful render

Build-sheet preparation embeds the selected master-data images into the generated
SVG/PNG. These image reads use `/api/files/<id>/content`; they are media reads,
not interactive API operations. A dense build can reference dozens of distinct
images in one preparation.

Since v1.0.12 the frontend permits the browser HTTP cache for these immutable
file-id URLs and limits embedding to six concurrent image reads. NGINX also
routes file-content reads through the dedicated `file_content` limiter instead
of consuming the `api_general` request budget. Do not fix recurrence by raising
or disabling the global API limiter.

If preparation succeeds once and subsequent attempts fail, inspect gateway
access logs for `/api/files/.../content` responses with HTTP 429/503 before
restarting containers. A gateway/container restart clears in-memory NGINX rate
state and can therefore mask this class of issue; browser cache clearing cannot
repair server-side rate state.

Relevant code:

- `frontend/src/modules/builds/buildPrintImageEmbedding.js`
- `infrastructure/nginx/default.conf`
- `infrastructure/scripts/quality/security_audit.py`

## Server-wide build printout cache

Since v1.0.13 a prepared build PNG is a shared derived cache, not a per-browser
artifact. The frontend first refreshes the build, renders the deterministic SVG
source in memory and derives `print-v<renderer>:<sha256>` from that source. If
the returned `BuildRead` already exposes the same cache key and source revision,
all authenticated viewers reuse the server copy instead of rasterizing again.
Only the owner or staff may populate/repair another build's cache.

The cache is deliberately bounded and fail-closed:

- `builds.updated_at` is the business revision and is never changed by cache
  writes. `printout_source_updated_at` records which revision was rendered.
- the download URL contains `cache_key`; a browser can therefore cache a
  versioned URL without serving an older build image after invalidation;
- the current PNG is stored under a checksum-versioned file name. A DB rollback
  cannot overwrite the previously committed cache file;
- a successful replacement deletes the previous file after commit; changing or
  deleting a build invalidates/removes its cache after commit;
- printouts count against the global upload quota and the configured minimum
  free-space reserve;
- the scheduled cleanup removes stale metadata, orphaned/legacy printout files
  and abandoned temporary uploads. Unexpected orphan candidates receive a one-hour
  grace window so cleanup cannot race an in-flight transactional cache write. The
  defaults are 24 h cleanup cadence and a 5 min initial delay.

A different locale or renderer output intentionally produces a different cache
key. The service retains only the currently selected cache variant for a build,
so alternate renders can replace each other but do not accumulate historical
versions. Whenever print layout/semantics change, bump
`BUILD_PRINT_RENDERER_VERSION` together with the change so old server-wide
entries cannot be mistaken for current output.

For failures, distinguish these cases before restarting services:

1. `404` on the versioned printout URL: stale/missing filesystem entry; an
   authorized prepare can rebuild it and the cleanup will remove stale metadata.
2. `409` on upload: the build changed during rendering or the same cache key
   produced different PNG content. Refresh and prepare again; do not overwrite
   the conflict manually.
3. storage-limit `400`: inspect global upload quota and filesystem free reserve;
   do not bypass the quota for printouts.
