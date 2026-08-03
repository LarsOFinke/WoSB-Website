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

### Bootstrap per SSH/SCP

Für den normalen Source-Setup müssen neben `infrastructure/` und `scripts/` auch die
Build-Kontexte `backend/`, `frontend/` und `spring-api/` übertragen werden. Für den
Git-freien Artifact-Deploy ist dagegen ein Minimal-Bootstrap möglich: Infrastruktur,
die beiden Root-Wrapper und `VERSION` genügen, sofern das Setup mit `--no-start` läuft.
Dadurch werden Host, Konfiguration, Zertifikate und systemd eingerichtet, aber keine
Anwendungs-Images gebaut.

Am zuverlässigsten bleiben die Dateirechte bei einem Git-Checkout erhalten:

```bash
git clone <REPOSITORY_URL> ~/royal-blackwater-fleet
cd ~/royal-blackwater-fleet
```

Bei einer reinen SCP-Übertragung müssen mindestens diese Pfade enthalten sein:

```text
backend/  frontend/  spring-api/  infrastructure/  scripts/
setup.sh  update.sh  VERSION
```

Für den Artifact-Bootstrap vom lokalen Rechner zunächst in ein temporäres Transferverzeichnis
übertragen (nicht als endgültigen Installationsort `/tmp` verwenden):

```bash
scp -r infrastructure setup.sh update.sh VERSION \
  USER@TESTSERVER:/tmp/rbf-bootstrap/
```

Falls die Übertragung die Ausführungsbits nicht erhält, vor dem Setup einmalig korrigieren:

```bash
chmod +x setup.sh infrastructure/setup.sh
find infrastructure/scripts -type f -name '*.sh' -exec chmod +x {} +
```

Ein fehlender Build-Kontext führt beim Setup zu einem Fehler wie
`unable to prepare context: path "/tmp/rbf-bootstrap/backend" not found`.
In diesem Fall wurde der Bootstrap ohne `--no-start` gestartet. Für ein bereits übertragenes
Artifact stattdessen fortsetzen mit:

```bash
cd /tmp/rbf-bootstrap
sudo ./setup.sh --profile full --no-start
sudo ./update.sh --artifact /tmp/rbf-deployment-1.0.0.tar.gz --seed
```

Der Bootstrap muss für systemd auf einem persistenten Pfad liegen, zum Beispiel
`/opt/royal-blackwater-fleet`; `/tmp` ist dafür nicht geeignet. `infrastructure/data/postgres`
wird vom Setup absichtlich dem PostgreSQL-Container zugewiesen und ist für normale Benutzer
nicht schreibbar. Das ist kein Quellcodeverlust.

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

### Installation vor der DNS-/SSL-Freischaltung

Die Erstinstallation kann vollständig erfolgen, bevor DNS oder ein öffentlich vertrauenswürdiges
Zertifikat bereitstehen:

```bash
sudo ./setup.sh \
  --profile core \
  --domain royal-blackwater-fleet.eu \
  --tls-mode self-signed
```

Das Setup erzeugt ein lokales Bootstrap-Zertifikat, startet den Stack und prüft ihn über HTTPS.
Browser zeigen dabei erwartungsgemäß eine Zertifikatswarnung. Dieses Zertifikat ist nur für die
Einrichtung, interne Tests und den temporären Betrieb gedacht; es ist keine öffentliche
Produktivfreigabe.

Auch spätere Image-Updates benötigen zunächst kein öffentliches Zertifikat. Das Artifact-Bundle
wird per SSH übertragen und mit `sudo ./update.sh --artifact ...` aktiviert. Der vorhandene
Bootstrap- oder Let's-Encrypt-Zertifikatsbestand bleibt dabei unverändert.

### Öffentliches Zertifikat später aktivieren

Sobald DNS auf den Webseiten-Server zeigt und TCP 80/443 erreichbar ist, wird Let's Encrypt direkt
auf diesem Server eingerichtet. Port 80 muss während der HTTP-01-Challenge erreichbar bleiben:

```bash
sudo certbot certonly \
  --non-interactive --agree-tos \
  --email admin@royal-blackwater-fleet.eu \
  --webroot --webroot-path infrastructure/data/acme \
  --config-dir infrastructure/data/letsencrypt/config \
  --work-dir infrastructure/data/letsencrypt/work \
  --logs-dir infrastructure/data/letsencrypt/logs \
  --cert-name royal-blackwater-fleet.eu \
  -d royal-blackwater-fleet.eu

sudo RENEWED_LINEAGE="$PWD/infrastructure/data/letsencrypt/config/live/royal-blackwater-fleet.eu" \
  ./infrastructure/scripts/tls/sync-certificate.sh
sudo ./infrastructure/scripts/checks/smoke-test.sh
```

Der Sync aktualisiert den Zertifikatsbestand atomar, lädt das Gateway neu und stellt den
Zertifikatsanbieter auf `letsencrypt`. Danach übernimmt der systemd-Timer die Verlängerungen.
Der Backup-Server ist an diesem Vorgang nicht beteiligt und benötigt weder das Zertifikat noch
den privaten Schlüssel.

Das Setup prüft Architektur, Speicher, Ports und Betriebssystem, installiert Docker/Host-Pakete,
erzeugt Secrets, baut Images, migriert/seedet PostgreSQL und richtet Firewall, TLS, systemd sowie
lokale Backups ein. Zusätzlich werden tägliche Security-Updates ohne automatische Neustarts
aktiviert. Der aufrufende Benutzer erhält keine root-äquivalenten Docker-Gruppenrechte.
`--regenerate-secrets` ist aus Sicherheitsgründen nur vor der ersten
PostgreSQL-Initialisierung erlaubt.

Bei einem Testlauf wurden nach erfolgreicher Installation folgende Host-Sicherheitswarnungen
ausgegeben: aktive SSH-Passwortauthentifizierung und ein nicht vollständig deaktivierter
SSH-Root-Login (`without-password`). Das Setup ändert diese Einstellungen absichtlich nicht.
Vor einer öffentlichen Freigabe zuerst einen geprüften Schlüsselzugang testen und anschließend
Passwortauthentifizierung sowie Root-Login nach der lokalen SSH-Richtlinie deaktivieren.

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
sudo docker compose --env-file infrastructure/.env -f infrastructure/compose.yml ps api secure-api gateway
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
