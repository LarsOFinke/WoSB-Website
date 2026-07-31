# Betrieb

## Diagnose

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
make infra-status
make infra-logs
```

Health-Endpunkte:

```text
GET /api/health
GET /api/health/ready
```

## Updates

Standardupdate mit automatischer Schemaerkennung:

```bash
sudo ./update.sh
```

Der Standardlauf baut zuerst das neue API-Image und vergleicht dessen Alembic-Head mit der
laufenden PostgreSQL-Datenbank. Ausstehende Migrationen werden automatisch erkannt, vorab durch ein
Datenbankbackup abgesichert und anschließend ausgeführt. Damit werden auch Migrationen nach einem
zuvor fehlgeschlagenen Deployment erneut erkannt, selbst wenn beim zweiten Lauf kein neuer Git-Diff
mehr entsteht.

Expliziter Migrations- und Seed-Lauf:

```bash
sudo ./update.sh --migrate --seed
```

`--seed` impliziert immer `--migrate`. Mit `--no-auto-migrate` wird ein Deployment bei einer
abweichenden Datenbankrevision abgebrochen; ein inkompatibles API-Image wird nicht gestartet.

Der Updater übernimmt Admin-Anforderungen erst nach dem exklusiven Lock, verweigert lokale
Git-Änderungen, nutzt Fast-Forward, schreibt während des Laufs einen Heartbeat, sichert vor
Datenbankarbeiten, hält die vorherigen Container-Images als Rollback-Punkt fest und führt nach
Migration und Deployment einen Schema-, Readiness- und HTTPS-Smoke-Test aus. Der Webbereich zeigt
absichtlich nur Vorgang, Zustand und Zeitpunkte. Commit-IDs, anfordernde Konten und Log-Auszüge
bleiben im Host-Protokoll beziehungsweise in den konfigurierten Webhook-Zustellungen und werden
nicht an den Browser ausgeliefert.

## Backup

```bash
./infrastructure/scripts/backup/backup-all.sh
```

Backups liegen unter `infrastructure/data/backups` und werden nach
`BACKUP_RETENTION_DAYS` aufgeräumt. Mindestens eine regelmäßige externe Kopie ist erforderlich.

Mit `BACKUP_RECOVERY_ENABLED=true` erzeugt derselbe Lauf zusätzlich ein einziges age-verschlüsseltes
Disaster-Recovery-Bundle. Es enthält Datenbank, Uploads/Betriebsdaten, `.env`, alle `.cfg`-Snapshots,
Let's-Encrypt-Konfiguration, root-seitige Backup-Secrets und ein vollständiges SHA-256-Manifest.
`BACKUP_AGE_RECIPIENT` ist ausschließlich der öffentliche Empfänger; der private Schlüssel darf nur
auf dem externen Backup-Gerät liegen. `BACKUP_PULL_EXPORT_DIR` und `BACKUP_PULL_EXPORT_USER` stellen
eine nur für den gewählten SSH-Benutzer lesbare verschlüsselte Kopie für SCP-Pull bereit.

Das verbindliche Windows-Pull- und Bare-Metal-Restore-Verfahren steht in
[`docs/DISASTER_RECOVERY.md`](DISASTER_RECOVERY.md).

### Remote-Anwendungsbackup aus dem Adminbereich

Administratoren können unter **Staff → Betrieb → Anwendungs-Backups** ein dediziertes
SSH-/SFTP-Ziel konfigurieren und ein frisches PostgreSQL-Backup sowie ein getrenntes Dateiarchiv
manuell auf eine andere Maschine übertragen. Bei aktivierter Recovery-Funktion wird zusätzlich das
verschlüsselte vollständige Recovery-Bundle übertragen. Das Dateiarchiv enthält immer `data/uploads` und,
sofern vorhanden, zusätzlich Zertifikate, Let's-Encrypt-Konfiguration und Uptime-Kuma-Daten.
Der Ablauf ist bewusst zweistufig:

1. Host und Port erfassen, den öffentlichen SSH-Host-Key ermitteln und dessen Fingerprint
   über einen zweiten vertrauenswürdigen Kanal prüfen.
2. Einen eingeschränkten SSH-Benutzer, ein bereits vorhandenes absolutes Zielverzeichnis
   und einen dedizierten privaten Schlüssel hinterlegen. Danach Verbindung testen und das
   Backup auslösen.

Der Host-Runner erstellt mit `backup-postgres.sh` einen komprimierten Dump und mit
`backup-data.sh` ein separates Dateiarchiv. Für jedes Artefakt wird eine `.sha256`-Datei erzeugt.
Archiv und Prüfsumme werden zunächst als `.part` übertragen, atomar umbenannt und anschließend auf
dem Zielserver mit `sha256sum -c` verifiziert. Das Zielkonto benötigt daher Schreibrechte im
Zielverzeichnis sowie die Möglichkeit, `sha256sum` auszuführen. Es sollte keine interaktive Shell
und keine Rechte außerhalb des Backup-Verzeichnisses besitzen.

Die API schreibt nur eine kurzlebige, mit Modus `0600` geschützte Anforderung. Der root-seitige
systemd-Runner übernimmt sie, speichert Schlüssel und `known_hosts` unter
`infrastructure/data/control/secrets/backup-remote/` und gibt an den Browser ausschließlich eine
bereinigte Verbindungszusammenfassung zurück. Verbindungsänderungen und manuelle Backup-Anforderungen
werden im Audit-Log protokolliert.

Status, Artefaktpfade und Fehler stehen im Adminbereich sowie auf dem Host unter:

```text
infrastructure/data/control/status/backup-status.json
infrastructure/data/control/status/backup.log
```

Für die Funktion müssen `rbf-hub-backup-admin.path` und
`rbf-hub-backup-admin.service` installiert sein. Ein erfolgreiches `sudo ./update.sh` installiert
und aktiviert beide Units automatisch.

## Discord-Webhook-Schlüssel

`infrastructure/.env` enthält `WEBHOOK_ENCRYPTION_KEYS`. Der erste, kommagetrennte
Fernet-Schlüssel verschlüsselt neue Discord-Webhook-Tokens; nachfolgende Schlüssel dienen der
Entschlüsselung während einer Rotation. Der Updater erzeugt den Schlüssel bei alten Installationen
automatisch. Die Datei bleibt mit Modus `0600` geschützt und muss getrennt vom Datenbankbackup
gesichert werden.

Rotation in einem Wartungsfenster:

1. neuen Schlüssel erzeugen und vor die bestehende Liste setzen;
2. API neu starten und den Maintenance-Start abwarten;
3. alle Webhooks testen und ein neues Datenbankbackup erstellen;
4. erst danach alte Schlüssel aus der Liste entfernen.

Ein Datenbankbackup ohne mindestens einen gültigen Schlüssel kann die gespeicherten Discord-Ziele
nicht wiederherstellen.

## Monitoring-Major-Upgrade

Uptime Kuma bleibt bis zur kontrollierten Datenmigration auf 1.23.16. Das verbindliche Verfahren
für Backup, Migration, Verifikation und Rollback steht in `docs/UPTIME_KUMA_2_MIGRATION.md`. Die
Image-Version darf nicht im Rahmen eines normalen unbeaufsichtigten App-Updates auf 2.x geändert
werden.

## Automatische Datenbereinigung

Der Maintenance-Lauf entfernt abgelaufene Sessions und wendet die in `backend/config/uploads.cfg`
konfigurierten Fristen auf Anwendungslogs, Audit-Historie, Webhook-Deliveries, Cookie-Einwilligungen
und Registrierungsanträge an. Die Standardwerte und betrieblichen Auswirkungen sind in
`docs/DATA_RETENTION.md` dokumentiert. Nach Änderungen an Fristen sollte der nächste Lauf beobachtet
und das Ergebnis über die Systemlogs geprüft werden.

## TLS

```bash
./infrastructure/scripts/tls/renew-certificate.sh
./infrastructure/scripts/tls/sync-certificate.sh
```

systemd-Timer übernehmen Erneuerung und Backups. Änderungen an `.env` mit `chmod 600` schützen und
nie in Git aufnehmen.


## Curating the New Captain Guide

Staff members can edit the New Captain Guide and add text sections, resource collections, direct guide links, and direct build links. Published guides and available builds are loaded when the editor opens, preventing stale session state from leaving the selectors empty. Linked resources remain database references, so renamed guides and builds automatically display their current titles.
