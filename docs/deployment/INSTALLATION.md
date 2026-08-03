# v1.0-Installation des Webseiten-Servers

Der Produktionsaufbau besteht aus zwei getrennten Hosts:

| Host | Aufgabe | Exponierte Dienste |
|---|---|---|
| Webseiten-Server | Gateway, Spring-API, FastAPI, PostgreSQL, lokale Backup-Orchestrierung | TCP 80/443 (optional 8443 nur LAN/VPN) |
| Backup-/Recovery-Server | verschlüsselte Backup-Sets, SFTP-Upload, read-only Recovery-Download | SSH/SFTP vom Webseiten-Server; kein Webdienst |

Die Sprachlaufzeiten bleiben in getrennten Containern: NGINX/Node für das Frontend,
Spring Boot/Java für die API-Fassade, FastAPI/Python für die verbleibenden
Fachmodule und PostgreSQL als eigener Datenbankdienst. Der Webseiten-Server muss
kein JDK, Maven, Node oder Python auf dem Host installieren; diese Laufzeiten
werden beim Image-Build beziehungsweise im Container verwendet. Das Recovery-Tool
wird ausschließlich auf dem zweiten Host installiert.

## 1. Host vorbereiten

Empfohlen werden Raspberry Pi 4/5, Raspberry Pi OS Lite 64-bit, mindestens 2 GiB RAM, eine SSD oder
eine hochwertige SD-Karte und eine feste DHCP-Zuordnung.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Für öffentlichen Betrieb müssen DNS sowie TCP 80/443 auf den Webseiten-Server zeigen. Der Monitoring-Port 8443
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

Das Spring-Backend wird mehrstufig im Container gebaut; auf dem Produktionshost sind daher weder
ein JDK noch Maven nötig. Der Build lädt die in `spring-api/pom.xml` festgelegten Abhängigkeiten und
erzeugt ein minimales Java-21-Runtime-Image. Für lokale Entwicklung werden JDK 21 und Maven 3.9+
benötigt; `make spring-test` löst die Projektabhängigkeiten auf und prüft die Installation.

Der Gateway bindet das Statusverzeichnis schreibgeschützt ein. Während dedizierter Updates,
Neustarts und produktiver Restores liefert er dadurch eine eigenständige statische RBF-503-Seite,
selbst wenn API oder Datenbank gerade nicht erreichbar sind. Reguläre Backups verursachen keine
Wartungsseite.

## 3. Abschluss

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
docker compose --env-file infrastructure/.env -f infrastructure/compose.yml ps api secure-api gateway
```

Mit den Daten aus `infrastructure/first-run-credentials.txt` anmelden, das Admin-Passwort ändern und
die Datei nach sicherer Ablage löschen.

Vor einer öffentlichen Freigabe sind außerdem Impressum und Datenschutzerklärung zu veröffentlichen,
DNS/TLS extern zu prüfen, ein SSH-Schlüsselzugang zu testen und das Backup-System einschließlich
Restore-Nachweis einzurichten. Die vollständige Trennung zwischen automatisierten Schritten und
Administrator-Gates steht im [Security- und Datenschutz-Audit](../audits/SECURITY_PRIVACY_AUDIT.md).

## Wechsel von einer historischen Datenbank

Die aktuelle Version startet mit einer aufgelösten Schema-Baseline. Historische Datenbanken werden
nicht direkt über Alembic weitergeführt. Vor der Umstellung müssen PostgreSQL und Uploads vollständig
gesichert und die fachlichen Daten in eine frisch initialisierte Datenbank importiert werden. Die
alte Datenbank darf erst nach erfolgreichem Doctor-, Smoke- und Fachtest außer Betrieb gehen.
