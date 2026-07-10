# Raspberry Pi first run

## 1. Prepare the device

Install a current 64-bit Raspberry Pi OS Lite or Debian image, enable SSH and ensure the Pi has
a stable LAN address or DHCP reservation.

## 2. Clone and start

```bash
sudo apt update
sudo apt install -y git
git clone <BLACKWATER_REPOSITORY_URL> ~/repositories/blackwater-hub
cd ~/repositories/blackwater-hub
sudo ./setup.sh --profile full
```

No application `.env` files need to be created manually. The setup script generates the
production configuration under `infrastructure/.env`.

## 3. Open the hub

The completion summary prints the detected URLs. The initial certificate is self-signed, so
accept the browser warning on trusted LAN devices.

The initial administrator credentials are written to:

```text
infrastructure/first-run-credentials.txt
```

Store them securely and delete that file.

## 4. Verify

```bash
make infra-status
curl --insecure https://<PI-IP>/api/health/ready
```

Expected API response:

```json
{"status":"ready","database":"postgresql"}
```

## 5. Back up before updates

```bash
make infra-backup
make infra-update
```

The update command uses `git pull --ff-only`, rebuilds images, reruns migrations and verifies
the final health endpoint.
