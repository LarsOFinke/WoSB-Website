# Royal Blackwater Fleet v1.0.0

Produktionsreifes Fleet-Operations-Portal für **World of Sea Battle** mit Vue 3, FastAPI,
PostgreSQL, NGINX und einem reproduzierbaren Raspberry-Pi-Deployment.

## Schnellstart auf dem Raspberry Pi

Voraussetzungen: Raspberry Pi OS Lite **64-bit** oder Debian/Ubuntu 64-bit, mindestens 2 GiB RAM,
8 GiB freier Speicher, DNS auf den Pi sowie weitergeleitete TCP-Ports 80 und 443.

```bash
git clone <REPOSITORY_URL> ~/royal-blackwater-fleet
cd ~/royal-blackwater-fleet
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
```

Das Setup installiert die Host-Abhängigkeiten, erzeugt Secrets, baut die Container, migriert und
seedet ausschließlich System- und Stammdaten in PostgreSQL, konfiguriert TLS, Firewall, systemd, Backups und optional Uptime Kuma. Die einmalig
erzeugten Zugangsdaten liegen mit Modus `0600` unter
`infrastructure/first-run-credentials.txt` und sollten nach sicherer Ablage gelöscht werden.

## Entwicklung

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.lock
pip install --no-deps -e .
cp .env.example .env
rbf-dev
```

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

## Qualitäts- und Betriebsbefehle

```bash
make test          # schnelle, deterministische Tests
make test-full     # Migration, Build und Infrastrukturchecks
make validate      # vollständige Release-Prüfung
make doctor        # Produktionsdiagnose auf dem Pi
make infra-backup  # Datenbank, Uploads und Betriebsdaten sichern
```

Normales Update der API mit verpflichtender Migration und idempotentem Stammdaten-Seed:

```bash
sudo ./update.sh
```

Der zentrale Updater ergänzt bei jedem API-Deployment automatisch Migration und Seed. Der
ausdrückliche Aufruf ist gleichwertig und für Runbooks besonders gut sichtbar:

```bash
sudo ./update.sh --migrate --seed
```

Repository-eigene Stammdaten können bei bewusstem Verwerfen aller Admin-Overrides repariert werden:

```bash
sudo ./update.sh --restore-seed-defaults
```

Eigene Stammdatensätze und Benutzerinhalte bleiben dabei erhalten. Dieselbe Funktion steht Admins
in der Stammdatenverwaltung als bestätigter Button zur Verfügung.

Im Admin-Panel stehen Standardupdate, explizite Migration und Migration mit Seed ebenfalls bereit. Die Website zeigt dabei nur einen datensparsamen Status; detaillierte Update-Ausgaben bleiben in Host-Logs und Webhooks.

## Projektstruktur

```text
backend/        FastAPI, SQLAlchemy, Alembic, fachliche Module und Tests
frontend/       Vue 3, modulare UI, Lokalisierung und deterministische JS-Tests
infrastructure/ Docker Compose, NGINX, TLS, Backup, systemd und Pi-Bootstrap
scripts/        einheitliche Test-, Validierungs- und Release-Werkzeuge
docs/           v1.0-Betriebs- und Entwicklungsdokumentation
.github/        CI, Releases, optionales Produktionsdeployment und Dependabot
```

## Dokumentation

- [Qualitätsstandards und Definition of Done](docs/development/QUALITY_STANDARDS.md)
- [Vollständiger Dokumentationsindex](docs/README.md)
- [Go-Live-Checkliste](docs/deployment/GO_LIVE.md)
- [Installation](docs/deployment/INSTALLATION.md)
- [Architektur](docs/architecture/ARCHITECTURE.md)
- [Entwicklung](docs/development/DEVELOPMENT.md)
- [Datenbank und Seeds](docs/development/DATABASE.md)
- [Kampf-DPM-Analyse](docs/audits/COMBAT_DPM_ANALYSIS.md)
- [Stammdaten-Go-Live-Review](docs/audits/MASTER_DATA_GO_LIVE_REVIEW.md)
- [Tests](docs/development/TESTING.md)
- [Betrieb](docs/deployment/OPERATIONS.md)
- [Disaster Recovery und Desktop-Backup](docs/deployment/DISASTER_RECOVERY.md)
- [Assistierte Backup-Server-Einrichtung](docs/deployment/BACKUP_SERVER_ENROLLMENT.md)
- PostgreSQL-Restores nutzen eine validierte Staging-Datenbank, atomaren Tausch und automatischen Rollback; vollständige Bare-Metal-Restores erhalten zusätzlich `.env`, `.cfg`, Uploads, Zertifikate und Host-Secrets im age-verschlüsselten Bundle.
- Frozen Recovery Tool für Windows und Linux: gemeinsame Quellen unter `tools/recovery-tool`, native Build-Wrapper unter `tools/windows/recovery-tool` und `tools/linux/recovery-tool`; Ubuntu erhält zusätzlich ein installierbares `.deb`, systemd-Pull und ein optionales rootless-Docker-PostgreSQL-Restore-Labor
- [GitHub CI/CD](docs/deployment/DEPLOYMENT.md)
- [Webhook-Betrieb](docs/integrations/outbound-webhooks.md)
- [Webhook-Nachrichten-Templates](docs/integrations/webhook-templates/README.md)
- [Sicherheit](SECURITY.md)
- [Änderungsverlauf](CHANGELOG.md)

## Lizenz und Hinweise

Siehe [NOTICE.md](NOTICE.md).

## Backup und Recovery

- [Backup-Server einrichten – Kurzleitfaden](docs/deployment/BACKUP_SETUP_QUICKSTART.md)
