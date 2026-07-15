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

## TLS

```bash
./infrastructure/scripts/tls/renew-certificate.sh
./infrastructure/scripts/tls/sync-certificate.sh
```

systemd-Timer übernehmen Erneuerung und Backups. Änderungen an `.env` mit `chmod 600` schützen und
nie in Git aufnehmen.


## Curating the New Captain Guide

Staff members can edit the New Captain Guide and add text sections, resource collections, direct guide links, and direct build links. Published guides and available builds are loaded when the editor opens, preventing stale session state from leaving the selectors empty. Linked resources remain database references, so renamed guides and builds automatically display their current titles.
