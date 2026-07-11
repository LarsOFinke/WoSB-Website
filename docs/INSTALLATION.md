# Installation auf dem Raspberry Pi

## 1. Host vorbereiten

Empfohlen werden Raspberry Pi 4/5, Raspberry Pi OS Lite 64-bit, mindestens 2 GiB RAM, eine SSD oder
eine hochwertige SD-Karte und eine feste DHCP-Zuordnung.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Für öffentlichen Betrieb müssen DNS sowie TCP 80/443 auf den Pi zeigen. Der Monitoring-Port 8443
sollte nur über LAN/VPN erreichbar sein.

## 2. Installation

```bash
sudo apt install -y git
git clone <REPOSITORY_URL> ~/royal-blackwater-fleet
cd ~/royal-blackwater-fleet
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
```

`--profile core` lässt Uptime Kuma weg. `--tls-mode auto` nutzt bis zur erfolgreichen
Domainvalidierung ein Bootstrap-Zertifikat. `--no-start` erzeugt Konfiguration und Services ohne
Containerstart.

Das Setup prüft Architektur, Speicher, Ports und Betriebssystem, installiert Docker/Host-Pakete,
erzeugt Secrets, baut Images, migriert/seedet PostgreSQL und richtet Firewall, TLS, systemd sowie
Backups ein. `--regenerate-secrets` ist aus Sicherheitsgründen nur vor der ersten
PostgreSQL-Initialisierung erlaubt.

## 3. Abschluss

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
```

Mit den Daten aus `infrastructure/first-run-credentials.txt` anmelden, das Admin-Passwort ändern und
die Datei nach sicherer Ablage löschen.

## Upgrade von 0.x auf v1.0

```bash
cd ~/royal-blackwater-fleet
sudo ./infrastructure/scripts/backup/backup-all.sh
sudo ./update.sh --migrate --seed
```

`infrastructure/data` und PostgreSQL niemals löschen. Die v1-Migration entfernt nur bekannte
Entwicklungs-/Beispielinhalte; der v1-Seed legt keine neuen Mock-Inhalte an.
