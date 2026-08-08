# Debugging und Incident-Runbooks

Diese Runbooks dokumentieren die Fehlerbilder, die beim Spring-Boot-Deployment
und beim Betrieb des Website-Servers tatsächlich aufgetreten sind. Sie sind
bewusst auf Diagnose und sichere nächste Schritte beschränkt; keine Anleitung
kopiert Secrets, Cookies oder Authorization-Header in Tickets.

- [Modulorientiertes Debugging](MODULE_DEBUGGING.md) – Schichtentrennung,
  Evidenzminimum und passende Regressionstest-Ebene
- [Deployment-Incidents](DEPLOYMENT_INCIDENTS.md) – bekannte konkrete Symptome,
  Ursachen und sichere nächste Schritte
- [Legacy-Build-Datenmigration](LEGACY_BUILD_DATA_MIGRATION.md) – geprüfter
  Build-only Python→Java-Teilrestore mit Dry-Run, semantischer FK-Auflösung und
  Test→Production-Promotion

## Schnelle Eingrenzung

Vom Ursprungssystem zuerst den interaktiven, redigierenden Collector verwenden:

```bash
./infrastructure/scripts/diagnostics/debug.sh
./infrastructure/scripts/diagnostics/debug.sh --area calendar --category http-500 --since 30m --tail 400
```

Ohne Flag nutzt er `.env.origin.test`; Production wird nur mit
`--production` und `.env.origin.production` ausgewählt. Die agententaugliche
Ausgabe landet lokal unter `.diagnostics/` und verändert das Zielsystem nicht.
Direkte Zielserverbefehle
sind nur der manuelle Fallback:

```bash
sudo systemctl status rbf-hub.service --no-pager
sudo journalctl -u rbf-hub.service -n 200 --no-pager
sudo /srv/rbf/current/infrastructure/scripts/services/status.sh
sudo /srv/rbf/current/infrastructure/scripts/checks/doctor.sh
sudo /srv/rbf/current/infrastructure/scripts/services/logs.sh api gateway
```

Bei einem fehlgeschlagenen Release zuerst die Aktivierungsdiagnose unter
`/srv/rbf/shared/deployments/failed-*.log` sichern. Container und Netzwerke erst
danach bereinigen; die Diagnose darf nicht durch `docker compose down` verloren
gehen.

Die ausführliche Sammlung steht in
[`DEPLOYMENT_INCIDENTS.md`](DEPLOYMENT_INCIDENTS.md).


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
