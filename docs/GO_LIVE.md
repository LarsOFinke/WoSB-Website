# Go-Live-Checkliste v1.0

## Vor dem Wartungsfenster

- `main` ist geschützt und CI vollständig grün.
- Ein Release-Tag und das zugehörige SHA-256-Artefakt liegen vor.
- DNS zeigt auf den Anschluss; TCP 80/443 werden an den Raspberry Pi weitergeleitet.
- Ein extern gespeichertes PostgreSQL-/Upload-Backup ist aktuell und testweise lesbar.
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

## Upgrade einer bestehenden 0.x-Installation

```bash
cd ~/royal-blackwater-fleet
sudo ./infrastructure/scripts/backup/backup-all.sh
sudo ./update.sh --migrate --seed
sudo ./infrastructure/scripts/checks/doctor.sh
```

Die v1-Migration entfernt ausschließlich bekannte, unveränderte Entwicklungs-/Beispielinhalte.
Eigenständig erstellte Beiträge, Builds, Guides, Gruppen und Termine bleiben erhalten.

## Funktionale Abnahme

- Anmeldung, Passwortwechsel und Rollenrechte
- Profil einschließlich Preferred Ships/Roles und Profilnotiz
- Build erstellen, bearbeiten und erneut öffnen
- Segel-, Laternen-, Crew-, Waffen- und Upgrade-Berechnung
- Guide/Forum-Beitrag erstellen und bearbeiten
- Squad-Events unter „My Squads → Upcoming Events“
- Admin-Stammdaten, Standard-Update sowie Update + Migration + Seed
- Cookie-Einwilligung akzeptieren, ablehnen und erneut öffnen
- Upload sowie öffentliche Asset-Auslieferung ohne 403

## Nach dem Start

- Health- und Readiness-Endpunkt beobachten.
- Logs und freie Datenträgerkapazität kontrollieren.
- Externes Backup und Uptime-Monitoring verifizieren.
- Erst nach erfolgreicher Abnahme Wartungsseite/Ankündigung entfernen.
