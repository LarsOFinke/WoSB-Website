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
Migration und Deployment einen Schema-, Readiness- und HTTPS-Smoke-Test aus.

## Backup

```bash
./infrastructure/scripts/backup/backup-all.sh
```

Backups liegen unter `infrastructure/data/backups` und werden nach
`BACKUP_RETENTION_DAYS` aufgeräumt. Mindestens eine regelmäßige externe Kopie ist erforderlich.

### Remote-Datenbankbackup aus dem Adminbereich

Administratoren können unter **Staff → Betrieb → Datenbank-Backups** ein dediziertes
SSH-/SFTP-Ziel konfigurieren und ein frisches PostgreSQL-Backup manuell übertragen.
Der Ablauf ist bewusst zweistufig:

1. Host und Port erfassen, den öffentlichen SSH-Host-Key ermitteln und dessen Fingerprint
   über einen zweiten vertrauenswürdigen Kanal prüfen.
2. Einen eingeschränkten SSH-Benutzer, ein bereits vorhandenes absolutes Zielverzeichnis
   und einen dedizierten privaten Schlüssel hinterlegen. Danach Verbindung testen und das
   Backup auslösen.

Der Host-Runner erstellt mit `backup-postgres.sh` einen komprimierten Dump, überträgt Dump
und `.sha256`-Datei zunächst als `.part`, benennt beide atomar um und führt auf dem Zielserver
`sha256sum -c` aus. Das Zielkonto benötigt daher Schreibrechte im Zielverzeichnis sowie die
Möglichkeit, `sha256sum` auszuführen. Es sollte keine interaktive Shell und keine Rechte außerhalb
des Backup-Verzeichnisses besitzen.

Die API schreibt nur eine kurzlebige, mit Modus `0600` geschützte Anforderung. Der root-seitige
systemd-Runner übernimmt sie, speichert Schlüssel und `known_hosts` unter
`infrastructure/data/control/secrets/backup-remote/` und gibt an den Browser ausschließlich eine
bereinigte Verbindungszusammenfassung zurück. Verbindungsänderungen und manuelle Backup-Anforderungen
werden im Audit-Log protokolliert.

Status und Fehler stehen im Adminbereich sowie auf dem Host unter:

```text
infrastructure/data/control/status/backup-status.json
infrastructure/data/control/status/backup.log
```

Für die Funktion müssen `rbf-hub-backup-admin.path` und
`rbf-hub-backup-admin.service` installiert sein. Ein erfolgreiches `sudo ./update.sh` installiert
und aktiviert beide Units automatisch.

## TLS

```bash
./infrastructure/scripts/tls/renew-certificate.sh
./infrastructure/scripts/tls/sync-certificate.sh
```

systemd-Timer übernehmen Erneuerung und Backups. Änderungen an `.env` mit `chmod 600` schützen und
nie in Git aufnehmen.


## Curating the New Captain Guide

Staff members can edit the New Captain Guide and add text sections, resource collections, direct guide links, and direct build links. Published guides and available builds are loaded when the editor opens, preventing stale session state from leaving the selectors empty. Linked resources remain database references, so renamed guides and builds automatically display their current titles.
