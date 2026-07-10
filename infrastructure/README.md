# Blackwater Infrastructure

This directory turns the application repository into a reproducible Raspberry Pi deployment.
It follows the modular principles of the separate
[`PI-Server-Infrastructure`](https://github.com/LarsOFinke/PI-Server-Infrastructure)
repository, but is specialized for the Blackwater application lifecycle.

## First run on a fresh Pi

Install Raspberry Pi OS Lite or Debian, enable SSH, then run:

```bash
git clone <BLACKWATER_REPOSITORY_URL> ~/repositories/blackwater-hub
cd ~/repositories/blackwater-hub
sudo ./setup.sh --profile full
```

The script performs as much of the first installation as possible:

1. installs Docker, Compose, Git, OpenSSL and UFW;
2. generates PostgreSQL and initial administrator credentials;
3. creates a self-signed TLS certificate for the detected hostname and LAN IP;
4. prepares persistent data directories and permissions;
5. configures the firewall for SSH, HTTP and HTTPS;
6. installs a systemd unit for boot-time startup;
7. builds frontend and backend images;
8. starts PostgreSQL and waits for its healthcheck;
9. runs Alembic migrations and idempotent seed data;
10. starts FastAPI and the NGINX gateway;
11. optionally starts Uptime Kuma;
12. executes an HTTPS/API/database smoke test.

Generated secrets are stored in `infrastructure/.env` and, for the first run only,
in `infrastructure/first-run-credentials.txt`. Both files are ignored by Git and use
mode `0600`. Move the credentials into a password manager and delete the first-run file.

## Profiles

```bash
sudo ./setup.sh --profile core  # app + PostgreSQL + NGINX
sudo ./setup.sh --profile full  # core + Uptime Kuma
```

Useful options:

```bash
sudo ./infrastructure/setup.sh \
  --hostname blackwater.example.org \
  --ip 192.168.178.50 \
  --admin-username commander

./infrastructure/setup.sh --skip-host --no-start
```

`--skip-host` is intended for development hosts where Docker is already installed.

## Service lifecycle

```bash
make infra-status
make infra-logs
make infra-backup
make infra-update
make infra-down
make infra-up
```

Direct commands are available below `infrastructure/scripts/`.

## Network model

- NGINX publishes ports 80 and 443.
- FastAPI is only exposed to the internal Docker network.
- PostgreSQL is internal and additionally bound to `127.0.0.1:15432` for optional SSH tunnels.
- Uptime Kuma is optional and bound to `127.0.0.1:3001`.

Example database tunnel:

```bash
ssh -L 5432:127.0.0.1:15432 pi@blackwater-host
```

## TLS

The first-run certificate is self-signed so that production cookies remain `Secure` from
the first boot. Browsers will show a trust warning. Replace these two files with a trusted
certificate when DNS and external reachability are ready:

```text
infrastructure/data/certs/fullchain.pem
infrastructure/data/certs/privkey.pem
```

Then restart the gateway:

```bash
./infrastructure/scripts/services/restart.sh gateway
```

## Backups

```bash
./infrastructure/scripts/backup/backup-postgres.sh
./infrastructure/scripts/backup/backup-data.sh
./infrastructure/scripts/backup/restore-postgres.sh infrastructure/data/backups/postgres/<file>.sql.gz
```

Backups remain local under `infrastructure/data/backups/`; the setup installs a daily 03:15 systemd timer and removes files older than `BACKUP_RETENTION_DAYS` (14 by default). A real production rollout should
copy them to another machine or encrypted remote storage.
