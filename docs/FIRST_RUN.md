# Raspberry Pi first run

## 1. Prepare the device

Install a current 64-bit Raspberry Pi OS Lite or Debian image, enable SSH and assign the Pi a stable
LAN address or DHCP reservation.

For the public domain, configure DNS and forward TCP ports 80 and 443 to the Pi before requesting a
Let's Encrypt certificate.

## 2. Clone and start

```bash
sudo apt update
sudo apt install -y git
git clone <RBV_REPOSITORY_URL> ~/repositories/royal-blackwater-vanguards
cd ~/repositories/royal-blackwater-vanguards
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-vanguards.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-vanguards.eu
```

No application `.env` files need to be created manually. The setup generates production
configuration under `infrastructure/.env`.

When DNS is not ready, start with:

```bash
sudo ./setup.sh --profile full --tls-mode auto
```

The hub then uses a self-signed bootstrap certificate. Run the explicit domain command later to
obtain and activate the trusted certificate without resetting PostgreSQL.

## 3. Open the services

```text
https://royal-blackwater-vanguards.eu       Fleet Hub
https://royal-blackwater-vanguards.eu:8443  Uptime Kuma
```

The initial administrator credentials are written to:

```text
infrastructure/first-run-credentials.txt
```

Store them securely and delete that file.

## 4. Verify

```bash
make infra-status
curl --fail https://royal-blackwater-vanguards.eu/api/health/ready
curl --fail --head https://royal-blackwater-vanguards.eu:8443/
systemctl status rbv-hub-cert-renew.timer
```

Expected API response:

```json
{"status":"ready","database":"postgresql"}
```

## 5. Update safely

```bash
make infra-backup
make infra-update
```

The update flow pulls fast-forward changes, rebuilds images, reruns migrations and verifies health.
The fleet seed migrates the former Blackwater Mercenaries slug in place, preserving fleet IDs and
memberships.

## Database credential isolation

The deployment controller removes inherited `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
and `DATABASE_URL` variables before Docker Compose starts. PostgreSQL, migration, seed and API then
read the same `infrastructure/.env`, preventing host variables from creating a password mismatch.
