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
  --profile core \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
```

`--profile core` ist die empfohlene öffentliche Basis und lässt die zusätzliche
Monitoring-Oberfläche weg. `--profile full` darf erst verwendet werden, wenn Uptime Kuma
administrativ eingerichtet und Port 8443 auf LAN/VPN begrenzt ist. `--tls-mode auto` nutzt bis zur erfolgreichen
Domainvalidierung ein Bootstrap-Zertifikat. `--no-start` erzeugt Konfiguration und Services ohne
Containerstart.

Das Setup prüft Architektur, Speicher, Ports und Betriebssystem, installiert Docker/Host-Pakete,
erzeugt Secrets, baut Images, migriert/seedet PostgreSQL und richtet Firewall, TLS, systemd sowie
lokale Backups ein. Zusätzlich werden tägliche Security-Updates ohne automatische Neustarts
aktiviert. Der aufrufende Benutzer erhält keine root-äquivalenten Docker-Gruppenrechte.
`--regenerate-secrets` ist aus Sicherheitsgründen nur vor der ersten
PostgreSQL-Initialisierung erlaubt.

## 3. Abschluss

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
```

Mit den Daten aus `infrastructure/first-run-credentials.txt` anmelden, das Admin-Passwort ändern und
die Datei nach sicherer Ablage löschen.

Vor einer öffentlichen Freigabe sind außerdem Impressum und Datenschutzerklärung zu veröffentlichen,
DNS/TLS extern zu prüfen, ein SSH-Schlüsselzugang zu testen und das Backup-System einschließlich
Restore-Nachweis einzurichten. Die vollständige Trennung zwischen automatisierten Schritten und
Administrator-Gates steht in [SECURITY_PRIVACY_AUDIT.md](SECURITY_PRIVACY_AUDIT.md).

## Wechsel von einer historischen Datenbank

Die aktuelle Version startet mit einer aufgelösten Schema-Baseline. Historische Datenbanken werden
nicht direkt über Alembic weitergeführt. Vor der Umstellung müssen PostgreSQL und Uploads vollständig
gesichert und die fachlichen Daten in eine frisch initialisierte Datenbank importiert werden. Die
alte Datenbank darf erst nach erfolgreichem Doctor-, Smoke- und Fachtest außer Betrieb gehen.
