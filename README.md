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
make infra-backup  # Datenbank und Uploads sichern
```

Normales Update mit automatischem Vergleich zwischen Datenbankrevision und neuem API-Image:

```bash
sudo ./update.sh
```

Ausstehende Alembic-Migrationen werden dabei automatisch gesichert und ausgeführt. Update mit
expliziter Migration und Stammdaten:

```bash
sudo ./update.sh --migrate --seed
```

Repository-eigene Stammdaten können bei bewusstem Verwerfen aller Admin-Overrides repariert werden:

```bash
sudo ./update.sh --restore-seed-defaults
```

Eigene Stammdatensätze und Benutzerinhalte bleiben dabei erhalten. Dieselbe Funktion steht Admins
in der Stammdatenverwaltung als bestätigter Button zur Verfügung.

Im Admin-Panel stehen Standardupdate, explizite Migration und Migration mit Seed ebenfalls bereit.

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

- [Go-Live-Checkliste](docs/GO_LIVE.md)
- [Installation](docs/INSTALLATION.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Entwicklung](docs/DEVELOPMENT.md)
- [Datenbank und Seeds](docs/DATABASE.md)
- [Stammdaten-Go-Live-Review](docs/MASTER_DATA_GO_LIVE_REVIEW.md)
- [Tests](docs/TESTING.md)
- [Betrieb](docs/OPERATIONS.md)
- [GitHub CI/CD](docs/DEPLOYMENT.md)
- [Webhook-Betrieb](docs/outbound-webhooks.md)
- [Webhook-Nachrichten-Templates](docs/webhook-templates/README.md)
- [Sicherheit](SECURITY.md)
- [Änderungsverlauf](CHANGELOG.md)

## Lizenz und Hinweise

Siehe [NOTICE.md](NOTICE.md).
