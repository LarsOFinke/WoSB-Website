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

Code ohne Schema-/Seed-Arbeit:

```bash
sudo ./update.sh
```

Release mit Migration und Stammdaten:

```bash
sudo ./update.sh --migrate --seed
```

Der Updater sperrt parallele Läufe, verweigert lokale Git-Änderungen, nutzt Fast-Forward, sichert vor
Datenbankarbeiten, baut Images, migriert/seedet nur explizit und führt anschließend einen Smoke-Test
aus. Die zwei Admin-Buttons rufen exakt diese festen Betriebsmodi auf.

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
