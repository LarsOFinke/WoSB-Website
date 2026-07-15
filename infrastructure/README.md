# RBF Infrastruktur

Docker Compose betreibt PostgreSQL, Alembic-Migrationen, den expliziten Stammdaten-Seed, FastAPI,
NGINX und optional Uptime Kuma. Der eigenständige Discord-Bot wird über einen kontrollierten
Host-Runner installiert, konfiguriert und aktualisiert.

Die öffentlichen Einstiegspunkte liegen eine Ebene höher im Repository:

```bash
cd /pfad/zum/repository
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu

sudo ./update.sh
```

Betriebs- und Diagnosebefehle innerhalb des Infrastruktur-Verzeichnisses:

```bash
cd infrastructure
./scripts/checks/lint.sh
./scripts/checks/doctor.sh
./scripts/services/status.sh
./scripts/backup/backup-all.sh
```

Runtime-Daten liegen ausschließlich unter `data/` und sind von Git sowie Release-Artefakten
ausgeschlossen. Die interne Modulaufteilung und die stabilen Delegationsziele sind in
[`ARCHITECTURE.md`](ARCHITECTURE.md) beschrieben. Weitere Betriebsdetails stehen in
`../docs/INSTALLATION.md`, `../docs/GO_LIVE.md` und `../docs/OPERATIONS.md`.
