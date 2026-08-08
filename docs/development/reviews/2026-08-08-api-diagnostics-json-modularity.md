# API-Diagnostik, Flyway-Regression und JSON-Modularisierung – 2026-08-08

## Ausgangslage

Der vollständige Maven-Testlauf brach in
`FlywayMigrationCompatibilityTest.upgradesAnExistingV1HistoryWithoutChangingOrReapplyingIt`
ab. Der Test erwartete fünf auszuführende Migrationen nach einer bestehenden V1-
Historie. Mit `V8__build_printout_cache.sql` existieren jedoch sechs ausstehende
Vorwärtsmigrationen (V3 bis V8). Flyway arbeitete korrekt; die feste Testzahl war
veraltet.

## Korrektur

Der Upgrade-Test leitet die erwartete Anzahl nun aus `Flyway.info().pending()` ab,
führt anschließend einen zweiten idempotenten `migrate()`-Lauf aus und prüft V1,
V7, V8 sowie die V8-Spalten explizit. Der Fresh-DB-Integrationspfad prüft V8 und
die neuen Printout-Cache-Spalten ebenfalls.

Die Build-Printout-Abdeckung wurde um Cache-Reuse und Invalidierung auf Service-
Ebene sowie einen echten HTTP/PostgreSQL/Dateisystem-Lifecycle erweitert. Damit
werden Build-Erzeugung, PNG-Speicherung, Download, identische Wiederverwendung,
Build-Versionierung, Cache-Invalidierung und Regeneration gemeinsam geprüft.

## API-Diagnostik

Jede `/api/`-Antwort erhält eine servergenerierte `X-Request-Id`. Zentral geloggte
`api_error`, `security_401` und `security_403` tragen dieselbe ID. Optionales
Lifecycle-Logging wird mit `RBF_HTTP_LIFECYCLE_LOGGING=true` aktiviert und enthält
nur Request-ID, Methode, normalisierte Route, Status und Laufzeit. Payloads,
Querywerte, Cookies, Client-IP und User-Agent bleiben ausgeschlossen. Die
Integrationstests aktivieren diese Diagnoseeigenschaft ausdrücklich; im normalen
Betrieb ist sie standardmäßig aus.

## JSON-KISS/SOLID

Große handgepflegte JSON-Monolithen wurden in verantwortungsbezogene Quellen
zerlegt:

- OpenAPI: eine Operation bzw. ein Schema pro Datei unter `openapi/source/`;
  `openapi/openapi.json` wird deterministisch zusammengesetzt.
- Build-Stats: eine Definition pro Datei unter `main/reference/build-stats/`.
- Build-Optionen und Schiffe: ein Seed-Eintrag pro Datei, gruppiert nach Kategorie
  bzw. Rate; numerische Präfixe konservieren die bisherige Katalogreihenfolge.

Ein Repository-Gate begrenzt diese handgepflegten JSON-Quellen auf 420 Zeilen und
verhindert die Rückkehr der entfernten Monolithen. Der Datenvergleich gegen das
Ausgangsrepository bestätigte identische Build-Stats (127), Build-Optionen (230)
und Schiffe (67); OpenAPI ist bis auf den Release-Versionssprung 1.0.13 → 1.1.0
semantisch identisch.

## Validierung

Erfolgreich ausgeführt wurden die Repository-, Dokumentations-, Security-,
Spring-Struktur-, Controller/OpenAPI-, SQL-Runtime-, Generator-, Java-21-Syntax-,
Infrastruktur-, Update-/Artifact-, TLS-, Python/Recovery- sowie Frontend-Gates.
Die Frontend-Suite meldete 167 Unit-Tests ohne Fehler und der Produktionsbuild war
erfolgreich.

Die aktuelle Ausführungsumgebung enthält kein Maven-3.9-Binary. Deshalb konnten
`mvn verify` und die neuen Testcontainers-Tests hier nicht erneut gestartet werden.
Der nächste CI-/Entwicklungsrechner mit Maven muss `mvn -f spring-api/pom.xml verify`
ausführen; dieser Lauf bleibt die autoritative Java-/Spring-/PostgreSQL-Prüfung.
