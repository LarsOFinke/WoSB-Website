# Raspberry Pi deployment

The previous manual systemd/SQLite deployment has been superseded by the integrated
container stack.

Use the first-run path:

```bash
git clone <BLACKWATER_REPOSITORY_URL> ~/repositories/blackwater-hub
cd ~/repositories/blackwater-hub
sudo ./infrastructure/setup.sh --profile full
```

Current deployment documentation:

- [First Run](FIRST_RUN.md)
- [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md)
- [Database Modes](DATABASE_MODES.md)
- [`infrastructure/README.md`](../infrastructure/README.md)

Production uses PostgreSQL and Alembic. SQLite remains the default local development database.
