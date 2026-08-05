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

`infrastructure/scripts/quality/tests/update-management.sh` prüft statisch, dass der Origin-Dispatcher
keine Backup-Überspring- oder Active-Replacement-Flags enthält und dass Installer
und Docker-Lifecycle die Backup-/Flyway-Schritte weiterhin aufrufen.

## SSH-Dispatcher ohne Passwort-Fallback

Die interaktive Passwortabfrage entstand, weil `.env.origin` den privaten
Anwendungsaccount verwendete und der Dispatcher keine feste Identity-Datei
übergeben hat. Der Dispatcher unterstützt jetzt `RBF_DEPLOY_IDENTITY_FILE` bzw.
`--identity-file` und setzt für alle SSH-/SCP-Aufrufe `BatchMode=yes` sowie
`IdentitiesOnly=yes`. Dadurch wird eine falsch eingerichtete Schlüsselstrecke
sofort sichtbar, statt in einer unbeaufsichtigten Ausführung nach einem Passwort
zu fragen. Nach dem einmaligen Bootstrap des dedizierten Accounts muss der
Zugang in einer zweiten Sitzung geprüft und erst dann in `.env.origin` aktiviert
werden.

Für frisch installierte Zielsysteme übernimmt `deploy.sh` diesen Übergang nun im
selben Lauf: Schlägt der Key-only-Preflight fehl, kann ein vorhandener
Initialbenutzer interaktiv oder per `--bootstrap-user` angegeben werden. Über
diese Verbindung werden ausschließlich der SSH-Provisioner und der Public Key
gestaged. Nach Einrichtung und SSH-Reload muss der neue `rbfadmin`-Preflight samt
`sudo -n` erfolgreich sein, bevor Build oder Release-Installation beginnen. Der
Initialbenutzer wird nicht in der Ursprungskonfiguration persistiert.

Der Bootstrap setzt keinen Passwort-Login voraus. Ohne explizite Bootstrap-
Identity übernimmt OpenSSH die Auswahl aus SSH-Konfiguration, Agent und
Standard-Keys und nutzt ein Passwort nur, wenn der Server dies erlaubt. Mit
`--bootstrap-identity-file` wird der angegebene VPS-Key exklusiv und im
Batch-Modus verwendet. Für initiale Root-Zugänge wird der Provisioner direkt,
für andere Accounts über `sudo` gestartet.
