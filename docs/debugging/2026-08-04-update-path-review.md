# Updatepfad und Datenbankerhalt

## Befund

Der bisherige Ursprungs-Dispatcher übergab `--skip-backup --no-backup` an den
Zielhost und entfernte mit `--replace-active` den aktiven Release vor der
Installation. Das bewahrte zwar `/opt/rbf/shared`, umging aber den vorgesehenen
koordinierten Pre-Deployment-Schutz.

## Korrektur

- `deploy-from-origin.sh` bereinigt nur fehlgeschlagene/inaktive Releases.
- Der aktive Release bleibt bis zum erfolgreichen Backup und Readiness-Test
  erhalten.
- Normale Updates übergeben weder `--skip-backup` noch `--no-backup`.
- `install-artifact.sh` ruft vor dem Releasewechsel
  `run-consistent-backup.sh` des bisherigen Releases auf.
- Schlägt Backup, Migration, Readiness oder Smoke-Test fehl, bleibt der alte
  Release aktiv bzw. wird zusammen mit den Backup-Artefakten wiederhergestellt.

## Daten- und Migrationspfad

1. PostgreSQL liegt als Bind-Mount unter `/srv/rbf/shared/data/postgres`.
2. Der Release verlinkt `infrastructure/data` auf `/srv/rbf/shared/data`.
3. Der Backup-Runner quiesziert die API, erstellt Dump, Dateisicherung,
   Recovery-/Restore-Preflight und Backup-Set-Manifest und startet die API
   anschließend wieder.
4. Erst danach wird der neue Release gebaut und atomar als `current` aktiviert.
5. Beim API-Start führt Flyway neue unveränderliche Migrationen aus; Hibernate
   bleibt auf `validate`.
6. Ein `docker compose down -v` wird im Updatepfad nicht verwendet.

## Erstinstallation und Root-Migration

Die automatische Zielinstallation hatte zunächst bei einem nicht-interaktiven
Erstlauf am Schutz `First installation requires explicit --no-backup`
angehalten. `setup_website.sh` erkennt nun eine wirklich leere Zielroot ohne
aktive oder verbliebene Releases und setzt die Erstinstallationsfreigabe intern.
Bei vorhandenen Releases oder einem aktiven `current` bleibt der koordinierte
Backup-Pfad unverändert.

Eine vorhandene Installation unter `/opt/rbf` wird vor der Environment-
Vorbereitung kontrolliert nach `/srv/rbf` verschoben. Der Migrationshelfer wird
sowohl im Release-Artefakt als auch separat vom Ursprungsserver übertragen,
damit auch ältere, bereits gebaute Artefakte fail-closed migriert werden können.

## Regression-Gates

`scripts/test-update-management.sh` prüft statisch, dass der Origin-Dispatcher
keine Backup-Überspring- oder Active-Replacement-Flags enthält und dass Installer
und Docker-Lifecycle die Backup-/Flyway-Schritte weiterhin aufrufen.
