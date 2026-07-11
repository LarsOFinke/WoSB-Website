# RBF Infrastruktur

Docker Compose betreibt PostgreSQL, Alembic-Migrationen, den expliziten Stammdaten-Seed, FastAPI,
NGINX und optional Uptime Kuma.

```bash
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
./scripts/checks/doctor.sh
./scripts/services/status.sh
./scripts/backup/backup-all.sh
```

Runtime-Daten liegen ausschließlich unter `data/` und sind von Git sowie Release-Artefakten
ausgeschlossen. Details: `../docs/INSTALLATION.md`, `../docs/GO_LIVE.md` und
`../docs/OPERATIONS.md`.
