# Cached Quick Overview – Debugging

Dieser Cache führt schnell zur kleinsten sicheren Evidenz. Ausführliche
Anleitungen stehen unter [docs/debugging](../docs/debugging/README.md); bekannte
Produktionsursachen im
[Incident-Index](../docs/debugging/DEPLOYMENT_INCIDENTS.md). Keine Rohlogs,
Cookies, Tokens, personenbezogenen Inhalte oder vollständigen IP-Adressen in den
Arbeitskontext übernehmen.

## Routing nach Symptom

| Symptom | Zuerst prüfen | Danach |
| --- | --- | --- |
| API 500 | zentrale `api_error`-Zeile, Methode/Pfad/Exceptiontyp | Route → operationId → Modul-Controller → Service → Repository/Mapper |
| 401 | `security_401`, Session-Cookie nur als vorhanden/nicht vorhanden | `SessionAuthenticationFilter`, aktiver User und Rollen-Fetch |
| 403 | `security_403`, Origin-/CSRF-Merkmale | Authority, Domain-Policy, CSRF und Host/Origin getrennt |
| 400/422 | Contractschema und `ApiExceptionHandler` | Transportbindung (400) von fachlicher Ablehnung (422) trennen |
| leere/falsche API-Antwort | Contract-Mapper und interne DB-Spalten | unbekannte Felder nicht durch Contractlockerung kaschieren |
| Startfehler | Properties-Binding, Flyway, Hibernate-`validate` | Readiness und erster Root-Cause-Stacktrace |
| Seed/Stammdaten | Seed-Key, Checksum, Override-Flag | Seeder idempotent erneut ausführen; keine Migration editieren |
| Legacy-Teilrestore/Migration | zuerst Dry-Run + erste Preflight-Exception | semantische FK-Auflösung prüfen; keine alten IDs oder kompletten Python-Dumps über Java-DB restaurieren |
| Fleet/Squad | Fleet-ID, Membership-Status, Rollen-Code/Capabilities | Bootstrap-Repair und AccessPolicy/HTTP-Test |
| Privacy/Cookie | Policy-Version, Entscheidung vorhanden, keine Schlüsselwerte | Retention, Exportausschlüsse, geschützte Route nach Löschung |
| Frontend lädt nicht | Browser-Konsole, fehlgeschlagener API-Status, Route | Page → Composable → API/Domain; Vite-Build und Browser-Smoke |
| Deployment/Update | lokal redigierte Diagnose, failed activation log | Artefaktversion, Compose, Readiness, Rollback; Daten nie löschen |

## Tokenarmer lokaler Ablauf

```bash
bash .agents/scripts/project-context.sh
rg -n "<operationId|Fehlertext|Klasse>" spring-api frontend contracts
bash .agents/scripts/check-changes.sh
```

Dann nur den fokussierten Test ausführen. Bei Fehlern liefern die Agenten-Gates
die letzten 200 Zeilen; vollständige Ausgabe erst gezielt mit
`AGENT_GATE_VERBOSE=1`. Lang laufende Sessions weiterverwenden, nicht denselben
Test parallel neu starten.

## Produktionsdiagnose

```bash
./infrastructure/scripts/diagnostics/debug.sh --area api --category http-500 --since 30m --tail 400
./infrastructure/scripts/diagnostics/debug.sh --area security --category auth --since 30m --tail 400
./infrastructure/scripts/diagnostics/debug.sh --area deployment --category errors --since 2h --tail 600
```

Gültige Bereiche: `overview`, `staff`, `calendar`, `api`, `security`, `gateway`,
`database`, `deployment`, `all`. Kategorien: `errors`, `warnings`, `http-500`,
`auth`, `migration`, `all`. Erst eng sammeln, dann bei Bedarf Zeitraum oder
Bereich erweitern. Der Collector liest standardmäßig `.env.origin.test`;
Production verlangt `--production` und `.env.origin.production`. Er schreibt remote nichts und
legt nur die lokal redigierte Ausgabe unter `.diagnostics/` ab.

## Bekannte stabile Fallstricke

- `/api/auth/me` ist öffentlich und liefert bei fehlender/ungültiger Session
  `200 null`; Session-Entzug an einer geschützten Route prüfen.
- Bean-Validation und JSON-/Query-Binding liefern zentral HTTP 400; fachliche
  Domainvalidierung kann 422 liefern.
- Multipart-Endpunkte separat behandeln: OpenAPI-Medientyp und generiertes
  `consumes` müssen übereinstimmen. Fehlender/kaputter Multipart-Body ist 400,
  falscher Content-Type 415 und Größenlimit 413; keiner dieser Transportfehler darf
  durch den generischen Handler zu 500 werden.
- Cookie-Einstellungen öffnen ohne gespeicherte Entscheidung absichtlich nicht
  automatisch, solange keine optionale Integration aktiv ist.
- Bei API-500ern die `X-Request-Id` der Antwort mit `api_error status=500 request_id=...`
  in Surefire/Serverausgabe korrelieren und den ersten eigenen Stack-Frame lesen. Der
  generische Response-Body ist keine Root Cause. Erfolgreiche Lifecycle-Logs nur gezielt
  mit `RBF_HTTP_LIFECYCLE_LOGGING=true` aktivieren; keine Payload-/Query-/IP-Daten loggen.
- Zusammengesetztes JDBC-SQL kann trotz gültigem Java erst zur Laufzeit scheitern:
  Fragmentgrenzen, Named-Parameter/Bindings und Alias/Spalten mit
  `python3 infrastructure/scripts/quality/audit_sql_runtime.py` prüfen; danach den
  betroffenen HTTP-Pfad plus `ApiSurfaceIntegrationTest` ausführen.
- Ein grüner Surface-Sweep ersetzt bei Review-/Admin-Flows keinen stateful Test.
  Referenz: Voraussetzung anlegen -> pending/list/read -> approve/reject/resolve ->
  Folge-Read/Login/Audit. Bereits verbrauchte Transition wiederholen und kontrolliertes
  4xx verlangen. Für diese Flows echte IDs statt 404-Sentinelwerten verwenden.
- Registration Access Review muss beide Zweige abdecken: `status=all`, Approve mit
  anschließendem Login/Approved-Read und Reject mit Rejected-Read.
- Optionale DB-Referenzen nie direkt als `Map.get(nullableLong(...))` verwenden. Ein
  pending/unreviewed Datensatz liefert dort `null`; insbesondere `Map.of()` wirft beim
  Lookup mit `null` eine NPE und maskiert einen gültigen Zustand als API-500.
- JDBC kann `DATE` als `java.sql.Date` liefern; am `RowValues`-Rand normalisieren.
- Interne Seed-/Relationsfelder vor strikter Contract-Konvertierung entfernen.
- Generierte Controller und Contracts nie direkt korrigieren; Generatorquelle
  ändern und `--check` ausführen.
- Flyway-Upgrade-Regressionen dürfen die Anzahl zukünftiger Migrationen nicht hart codieren.
  Vor dem Upgrade `Flyway.info().pending()` als erwartete Menge verwenden, danach einen
  zweiten `migrate()`-Lauf mit `0` Änderungen und die fachlich wichtigen Versionen/Spalten
  explizit auf genau einmalige Anwendung prüfen. Fresh-DB und V1-Upgrade bleiben getrennte
  Testpfade.
- Legacy-Build-Daten als logische Migration behandeln: exakt dieselbe geprüfte SQL-Datei
  zuerst testseitig Dry-Run -> Commit -> UI/API verifizieren und danach productionseitig
  erneut Dry-Run -> Commit. Schiffe/Optionen/Rollen/Features semantisch auflösen; historische
  numerische IDs, User-/Auth-Daten und Masterdata niemals aus dem Python-Komplettdump übernehmen.
  Runbook: `docs/debugging/LEGACY_BUILD_DATA_MIGRATION.md`.
- Produktionsdaten, Volumes, `shared/data` und aktive Releases sind keine
  zulässigen Debug-Cleanup-Ziele.

## Cache-Aktualisierung

Neue wiederkehrende Ursache erst nach reproduziertem Fehler, Root-Cause-Fix und
Regressionstest hier knapp ergänzen; die ausführliche Begründung gehört in ein
Runbook. Anschließend `bash .agents/scripts/check-cache.sh` und
`bash .agents/scripts/check-docs.sh` ausführen.

### Build print/image preparation
- Build print preparation may embed dozens of master-data images from `/api/files/<id>/content`.
- These media reads must not consume the interactive `api_general` NGINX rate budget. They use the dedicated bounded `file_content` zone.
- The frontend embedding path must retain HTTP caching and bounded concurrency (currently 6); do not restore `cache: 'no-store'` or unbounded `Promise.all()` fetching for image resources.
- Symptom pattern: one prepare succeeds, later prepares fail, browser cache clearing does not help, gateway/server restart temporarily helps. Check gateway access logs for file-content HTTP 429/503 before changing application caches.
- Preserve the global API limiter; fix media routing/embedding behavior rather than weakening general anti-abuse controls.

### Build-Printout-Cache (seit v1.0.13)

Build-PNGs sind ein serverweiter **Derived Cache**. Diagnose niemals als
Benutzer-/Browsercache beginnen. Der Client bildet aus Renderer-Version +
tatsächlich gerendertem SVG den Key `print-v<version>:<sha256>` und darf einen
Server-Hit nur verwenden, wenn `printout_cache_key` und
`printout_source_updated_at == updated_at` zum frisch geladenen Build passen.
Die URL trägt den `cache_key`, damit der HTTP-Cache keine alte Revision unter
einer unveränderten URL wiederverwenden kann.

Invarianten:

- Cache-Speichern darf `builds.updated_at` niemals verändern.
- PUT sperrt die Build-Zeile (`FOR UPDATE`), prüft die Quellrevision und lässt
  Cache-Population nur durch Owner/Staff zu.
- PNG-Dateien sind checksum-versioniert; DB-Commit wählt die gültige Datei.
  Rollback löscht die neue Datei, Commit löscht die vorige Datei.
- Build-Update/Rollenänderung invalidiert Metadaten und Datei nach Commit;
  Build-Löschung entfernt alle zugehörigen Printout-Dateien nach Commit.
- Global-Quota und `UPLOAD_MINIMUM_FREE_MB` gelten auch für Printouts.
- Scheduled Cleanup entfernt stale DB-Metadaten, Orphans, alte stabile
  `build-<id>.png`-Dateien und `.upload`-Fragmente; frische Orphan-Kandidaten
  erhalten eine Stunde Grace Window gegen Rennen mit laufenden Cache-Commits.
- Layout-, Semantik- oder sonstige Renderänderungen müssen
  `BUILD_PRINT_RENDERER_VERSION` bumpen. Gleiche Cache-Keys dürfen nie
  unterschiedliche PNG-Inhalte ergeben; der Server antwortet sonst 409.

Symptom `Prepare einmal erfolgreich, danach Fehler` zuerst getrennt prüfen:
Media-Rate-Limit (429/503, v1.0.12) versus Cache-Lifecycle (404/409/Quota).
Ein Container-Neustart ist keine Cache-Bereinigungsstrategie.
