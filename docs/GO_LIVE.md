# Go-Live-Checkliste v1.0

## Vor dem Wartungsfenster

- `main` ist geschützt und CI vollständig grün.
- Ein Release-Tag und das zugehörige SHA-256-Artefakt liegen vor.
- DNS zeigt auf den Anschluss; TCP 80/443 werden an den Raspberry Pi weitergeleitet.
- Ein extern gespeichertes, entschlüsseltes und vollständig manifestgeprüftes Recovery-Bundle ist aktuell.
- Der private age-Recovery-Schlüssel liegt auf zwei getrennten verschlüsselten Datenträgern und nicht auf dem Pi.
- Aktive Kühlung, zuverlässiges 5,1-V-Netzteil, SSD/hochwertiger Datenträger und ausreichende Belüftung sind vorhanden.
- GitHub-Deploy-Secrets und der dedizierte SSH-Schlüssel sind eingerichtet, falls CD genutzt wird.
- Datenschutzerklärung, Impressum, Cookie-Kategorien und tatsächlich verwendete Drittanbieter sind geprüft.

## Neue Installation

```bash
git clone <REPOSITORY_URL> ~/royal-blackwater-fleet
cd ~/royal-blackwater-fleet
sudo ./setup.sh \
  --profile core \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
```

Danach:

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
sudo ./infrastructure/scripts/checks/smoke-test.sh
```

Das optionale Full-Profil mit Uptime Kuma wird erst nach der administrativen Einrichtung und einer
Beschränkung des Monitoring-Ports auf LAN/VPN aktiviert. Der Host-Doctor prüft automatische
Security-Updates, Firewall-Defaults und root-äquivalente Docker-Gruppenmitgliedschaften mit.

Das erste Admin-Passwort sicher ablegen, sofort ändern und
`infrastructure/first-run-credentials.txt` löschen.

## Wechsel von einer historischen Installation

Die aufgelöste Schema-Baseline unterstützt keinen direkten Alembic-Upgradepfad aus der alten
Migrationskette. Für bestehende Installationen gilt daher:

1. vollständiges PostgreSQL- und Upload-Backup erstellen;
2. Datenexport in einer Kopie prüfen;
3. eine neue Datenbank mit `0001_baseline` aufbauen;
4. fachliche Daten kontrolliert importieren;
5. Seed und Doctor/Smoke-Test ausführen.

Die alte Datenbank bleibt bis zur vollständigen Abnahme unverändert als Rollback-Quelle erhalten.

## Funktionale Abnahme

- Anmeldung, Passwortwechsel und Rollenrechte
- Profil einschließlich Preferred Ships/Roles und Profilnotiz
- Build erstellen, bearbeiten und erneut öffnen
- Event-Smoke-Test: Leopard + Ice Lantern ergibt 10,1 Geschwindigkeit, 17.325 Laderaum und 2.142 Haltbarkeit
- Segel-, Laternen-, Crew-, Waffen- und Upgrade-Berechnung
- Guide/Forum-Beitrag erstellen und bearbeiten
- Squad-Events unter „My Squads → Upcoming Events“
- Admin-Stammdaten, Standard-Update sowie Update + Migration + Seed
- Cookie-Einwilligung akzeptieren, ablehnen und erneut öffnen
- Upload-Auslieferung über `/api/files/{id}/content`: Guide-/Forum-/Master-Data-Dateien anonym lesbar, private Uploads anonym mit 401; Legacy-Links verhalten sich identisch

## Kontrollierter 503-Wartungsmodus

Server-Updates, kontrollierte API-Neustarts und die produktive Aktivierungsphase eines
PostgreSQL-Restores schalten automatisch den statischen Wartungsmodus ein. NGINX bleibt dabei
erreichbar und liefert für Website und API HTTP `503 Service Unavailable`, `Retry-After: 120`,
`Cache-Control: no-store` sowie die eigenständige RBF-Wartungsseite aus. Normale Backups laufen
ohne Wartungsmodus, weil sie die Website nicht absichtlich abschalten.

Für ein manuelles Wartungsfenster kann der Host-Administrator denselben atomaren Mechanismus nutzen:

```bash
sudo env PYTHONPATH="$PWD/backend/src" python3 -m app.cli.maintenance_mode \
  enable --status-dir infrastructure/data/control/status --reason manual
sudo env PYTHONPATH="$PWD/backend/src" python3 -m app.cli.maintenance_mode \
  disable --status-dir infrastructure/data/control/status
```

Die Datei `maintenance-mode.json` ist der einzige Schalter. Fehlerpfade und Rollbacks entfernen
sie defensiv; falls ein Host hart ausfällt, kann der Administrator sie mit dem zweiten Befehl oder
direkt aus `infrastructure/data/control/status/` entfernen.

Die API veröffentlicht ihre Readiness vor zeitaufwendigen Aufräumarbeiten und
Webhook-Nachlieferungen. Der Update-Runner wartet bis zu drei Minuten und hält
bei einem Fehlschlag automatisch Containerstatus sowie die letzten API-Logs im
`update.log` fest. Damit ist ein echter Startfehler von einem langsamen Start
ohne zusätzliche Diagnosebefehle unterscheidbar.

Jedes Wartungsfenster erzeugt die abonnierbaren Webhook-Ereignisse
`system.maintenance.started` und `system.maintenance.ended`. Das gilt auch für
manuelle CLI-Wartungen, Restores, Neustarts sowie fehlgeschlagene Updates und
Rollbacks. Die Host-Seite legt diese Ereignisse atomar in einer Outbox ab; die
API übernimmt sie spätestens nach 15 Sekunden. Bei einer vorübergehend nicht
verfügbaren Datenbank bleibt das Ereignis für den nächsten Versuch erhalten.

`BACKUP_OFFSITE_DIR` bezeichnet ausschließlich ein optional lokal eingehängtes
Offsite-Dateisystem. Ein über die Administration eingerichtetes Backup-Ziel ist
eine separate SFTP-Konfiguration. Pre-Update-Backups übertragen ihr vollständig
committetes und verifiziertes Backup-Set nun ebenfalls über diese SFTP-Verbindung;
der Set-Manifest wird dabei zuletzt als Remote-Commit-Marker veröffentlicht.

Nach dem Git-Fast-Forward lädt der laufende Host-Runner seine Migrations-,
Backup-, Wartungs- und Rollback-Funktionen aus der neuen Revision erneut. Damit
werden neue Alembic-Revisionen bereits im selben Update erkannt und angewendet;
ein zweiter Update-Lauf ist nicht erforderlich.

## Nach dem Start

- Health- und Readiness-Endpunkt beobachten.
- Logs und freie Datenträgerkapazität kontrollieren.
- Externes Recovery-Bundle auf dem Windows-Backupgerät abrufen und vollständig prüfen.
- Uptime-Monitoring, Temperatur und `vcgencmd get_throttled` verifizieren.
- Prüfen, dass `infrastructure/data/control/status/maintenance-mode.json` nicht mehr vorhanden ist.
