# Raspberry Pi deployment

The old manual systemd/SQLite deployment has been replaced by the integrated container stack.
Production uses PostgreSQL and Alembic; SQLite remains the local development default.

```bash
git clone <RBF_REPOSITORY_URL> ~/repositories/royal-blackwater-fleet
cd ~/repositories/royal-blackwater-fleet
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
```

For a LAN-only test or while DNS is being prepared:

```bash
sudo ./setup.sh --profile full --tls-mode auto
```

Current deployment documentation:

- [First Run](FIRST_RUN.md)
- [Production Checklist](PRODUCTION_CHECKLIST.md)
- [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md)
- [Database Modes](DATABASE_MODES.md)
- [`infrastructure/README.md`](../infrastructure/README.md)
