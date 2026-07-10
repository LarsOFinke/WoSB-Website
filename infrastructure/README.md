# Royal Blackwater Vanguards Infrastructure

This directory turns the RBV application repository into a reproducible Raspberry Pi deployment.
It adapts the modular principles of
[`PI-Server-Infrastructure`](https://github.com/LarsOFinke/PI-Server-Infrastructure)
to the Royal Blackwater Vanguards application lifecycle.

## First run on a fresh Pi

Install Raspberry Pi OS Lite or Debian, enable SSH, assign a stable LAN address, and clone the
repository:

```bash
git clone <RBV_REPOSITORY_URL> ~/repositories/royal-blackwater-vanguards
cd ~/repositories/royal-blackwater-vanguards
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-vanguards.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-vanguards.eu
```

The script:

1. installs Docker, Compose, Certbot, Git, OpenSSL and UFW;
2. generates PostgreSQL and initial administrator credentials;
3. creates a self-signed bootstrap certificate;
4. prepares persistent data directories and permissions;
5. configures the firewall for SSH, HTTP, HTTPS and optional monitoring;
6. installs systemd units for startup, backups and certificate renewal;
7. builds frontend and backend images;
8. starts PostgreSQL and waits for its healthcheck;
9. runs Alembic migrations and idempotent seed data;
10. starts FastAPI, NGINX and optional Uptime Kuma;
11. validates the bootstrap stack;
12. requests a Let's Encrypt certificate through HTTP-01/webroot;
13. reloads the gateways and performs a final TLS/API/database smoke test.

Generated secrets live in `infrastructure/.env` and, for the first run only, in
`infrastructure/first-run-credentials.txt`. Both are ignored by Git and use mode `0600`.
Move the credentials to a password manager and delete the first-run file.

## DNS and router prerequisites

For `TLS_MODE=letsencrypt`:

- `royal-blackwater-vanguards.eu` must resolve to the public IP of the server connection;
- TCP port 80 must reach the Pi for the ACME HTTP-01 challenge;
- TCP port 443 must reach the Pi for the application;
- carrier-grade NAT or a blocked inbound port 80 prevents HTTP-01 validation.

Use `--tls-mode auto` while DNS or forwarding is being prepared. The application remains usable
with its self-signed bootstrap certificate and a later setup run can obtain the public certificate.

## Profiles and options

```bash
sudo ./setup.sh --profile core  # app + PostgreSQL + NGINX
sudo ./setup.sh --profile full  # core + Uptime Kuma
```

```bash
sudo ./infrastructure/setup.sh \
  --domain royal-blackwater-vanguards.eu \
  --ip 192.168.178.50 \
  --admin-username commander \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-vanguards.eu

./infrastructure/setup.sh --skip-host --no-start
```

`--letsencrypt-staging` uses the ACME staging service for deployment tests. Its certificate is
intentionally not browser-trusted.

## Network model

- NGINX publishes ports 80 and 443.
- FastAPI is only exposed to the internal Docker network.
- PostgreSQL is internal and additionally bound to `127.0.0.1:15432` for SSH tunnels.
- Uptime Kuma remains bound to `127.0.0.1:3001` and is exposed through a dedicated TLS gateway on
  `https://royal-blackwater-vanguards.eu:8443` when the `full` profile is active.
- The monitoring gateway joins the public ingress network and private service network; Kuma itself
  is never directly exposed to the LAN.

Keep monitoring restricted to LAN/VPN when possible. PostgreSQL deliberately has no public web UI.

Example database tunnel:

```bash
ssh -L 15432:127.0.0.1:15432 pi@royal-blackwater-vanguards.eu
```

## TLS lifecycle

The gateway starts with these stable certificate paths:

```text
infrastructure/data/certs/fullchain.pem
infrastructure/data/certs/privkey.pem
```

Certbot stores its managed state under:

```text
infrastructure/data/letsencrypt/
```

Successful issuance or renewal copies the current lineage into the stable gateway paths and reloads
NGINX. `rbv-hub-cert-renew.timer` checks twice daily. Manual commands:

```bash
sudo ./infrastructure/scripts/tls/renew-certificate.sh
sudo systemctl status rbv-hub-cert-renew.timer
```

## Service lifecycle

```bash
make infra-status
make infra-logs
make infra-backup
make infra-update
make infra-down
make infra-up
```

## Backups

```bash
./infrastructure/scripts/backup/backup-postgres.sh
./infrastructure/scripts/backup/backup-data.sh
./infrastructure/scripts/backup/restore-postgres.sh infrastructure/data/backups/postgres/<file>.sql.gz
```

Backups remain local under `infrastructure/data/backups/`. The daily timer removes files older than
`BACKUP_RETENTION_DAYS` (14 by default). Production should additionally copy encrypted backups to
another machine or remote storage.
