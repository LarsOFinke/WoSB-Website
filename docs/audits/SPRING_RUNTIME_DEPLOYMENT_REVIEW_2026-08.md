# Spring-Runtime-, Deployment- und Recovery-Prüfung (2026-08)

## Ergebnis

Die Spring-Boot-Laufzeit ist lokal startfähig und wurde gegen PostgreSQL 16 mit
Flyway, Hibernate-Validierung, idempotentem Stammdaten-Seed, Bootstrap-Admin,
Health-/Readiness-Endpunkten und einer unauthentifizierten 401-Grenze geprüft.
Das Release-Artefakt ist source-frei, inventarisiert und gegen Manipulation
geschützt. Ein daraus gebauter API-/NGINX-Stack erreichte im isolierten Compose-
Test `{"status":"ready"}`; die Testdatenbank meldete Flyway-Version `1`.

## Behobene Migrationsfunde

- Spring Boot 4 benötigt den separaten `spring-boot-starter-flyway` sowie das
  PostgreSQL-Flyway-Modul; der direkte Flyway-Kern allein aktiviert die
  Auto-Konfiguration nicht.
- Hikari-Zeitwerte sind als Millisekunden konfiguriert, damit der Start nicht an
  der Boot-4-Bindung von `10s`/`3s` scheitert.
- Mehrfachkonstruktoren in `RaidHelperHttpClient` und `FernetSecretBox` sind für
  Spring eindeutig als Constructor Injection markiert.
- MapStruct erhält die explizite User-ID-Zuordnung; Seed-JSON darf nullable
  Felder enthalten; Seed-Effekt-Inserts schreiben die im Basisschema geforderten
  Zeitstempel.
- Build-Stat-Berechnungen behandeln fehlende optionale Maps und behalten bei
  ganzzahliger Rundung den korrekten Zahltyp.

## Betriebsvertrag

1. CI führt `mvn verify`, Frontend-Test/Build sowie die Infrastruktur-,
   Artefakt-, Tamper- und Recovery-Gates aus.
2. `build-artifact.sh` erzeugt ein versioniertes Tarball mit `manifest.json`,
   `SHA256SUMS`, Spring-JAR, Frontend-`dist` und minimalen Runtime-Dateien.
3. `install-artifact.sh` prüft zuerst äußere und innere Prüfsummen, extrahiert
   sicher, baut nur die Runtime-Images und schaltet den Release-Symlink atomar.
   Bei einem aktiven Vorgänger wird vorab ein koordiniertes Backup inklusive
   Restore-Preflight erzeugt. `--no-backup` ist nur bei der Erstinstallation
   ohne aktiven Release zulässig.
4. `rollback-release.sh` verwendet die im Deployment-Zustand referenzierten
   Vorgänger-, PostgreSQL- und Datei-Backups. Lock-Signale verhindern dabei
   Deadlocks zwischen Update, Backup und Restore.
5. Recovery akzeptiert ausschließlich `--yes` als Aktivierungsbestätigung,
   validiert Argumente vor `realpath`, unterstützt fehlende optionale Datei-
   Module und installiert bei bestehendem `current` nicht fälschlich mit
   `--no-backup`.

## Noch bewusst nicht automatisiert

Ein echter Host-Go-Live mit systemd, produktiven TLS-Zertifikaten, externem
Backup-Ziel und Datenverlust-Simulation wurde nicht ausgeführt, weil er die
Produktionsumgebung verändert. Er bleibt als separater Go-Live-/Recovery-
Übungsschritt auf einem Staging-Host erforderlich.
