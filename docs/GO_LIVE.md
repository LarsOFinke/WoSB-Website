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
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode letsencrypt \
  --letsencrypt-email admin@royal-blackwater-fleet.eu
```

Danach:

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
sudo ./infrastructure/scripts/checks/smoke-test.sh
```

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

## Nach dem Start

- Health- und Readiness-Endpunkt beobachten.
- Logs und freie Datenträgerkapazität kontrollieren.
- Externes Recovery-Bundle auf dem Windows-Backupgerät abrufen und vollständig prüfen.
- Uptime-Monitoring, Temperatur und `vcgencmd get_throttled` verifizieren.
- Erst nach erfolgreicher Abnahme Wartungsseite/Ankündigung entfernen.
