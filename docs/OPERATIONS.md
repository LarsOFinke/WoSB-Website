# Betrieb

## Diagnose

```bash
sudo ./infrastructure/scripts/checks/doctor.sh
make infra-status
make infra-logs
```

Health-Endpunkte:

```text
GET /api/health
GET /api/health/ready
```

Der öffentliche Healthvertrag bleibt fachlich bei FastAPI, wird aber über die zentrale Spring-
API-Fassade weitergereicht. Spring Boot stellt zusätzlich nur im internen Compose-Netz
`/actuator/health/readiness` bereit; NGINX veröffentlicht den Actuator nicht. Status
und Logs des Sicherheitsdienstes werden mit `docker compose ... ps secure-api` beziehungsweise
`docker compose ... logs secure-api` geprüft. Ein Ausfall sperrt Login, Logout, Passwortwechsel und
Sessionabfrage, während nicht betroffene öffentliche Python-Inhalte weiter erreichbar bleiben.

## Updates

Standardupdate mit automatischer Schemaerkennung:

```bash
sudo ./update.sh
```

Der Standardlauf baut zuerst das neue API-Image und vergleicht dessen Alembic-Head mit der
laufenden PostgreSQL-Datenbank. Ausstehende Migrationen werden automatisch erkannt, vorab durch ein
Datenbankbackup abgesichert und anschließend ausgeführt. Damit werden auch Migrationen nach einem
zuvor fehlgeschlagenen Deployment erneut erkannt, selbst wenn beim zweiten Lauf kein neuer Git-Diff
mehr entsteht.

Expliziter Migrations- und Seed-Lauf:

```bash
sudo ./update.sh --migrate --seed
```

`--seed` impliziert immer `--migrate`. Mit `--no-auto-migrate` wird ein Deployment bei einer
abweichenden Datenbankrevision abgebrochen; ein inkompatibles API-Image wird nicht gestartet.

Der Updater übernimmt Admin-Anforderungen erst nach dem exklusiven Lock, verweigert lokale
Git-Änderungen, nutzt Fast-Forward, schreibt während des Laufs einen Heartbeat, sichert vor
Datenbankarbeiten, hält die vorherigen Container-Images als Rollback-Punkt fest und führt nach
Migration und Deployment einen Schema-, Readiness- und HTTPS-Smoke-Test aus. Der Webbereich zeigt
absichtlich nur Vorgang, Zustand und Zeitpunkte. Commit-IDs, anfordernde Konten und Log-Auszüge
bleiben im Host-Protokoll beziehungsweise in den konfigurierten Webhook-Zustellungen und werden
nicht an den Browser ausgeliefert.

Bei einer Migration hält der Updater die laufende API bereits vor dem konsistenten Backup an und
lässt sie bis nach `alembic upgrade head` sowie der exakten Schemaprüfung gestoppt. Dadurch kann ein
unter demselben Compose-Tag neu gebautes API-Image nicht zwischen Backup und Migration vorzeitig
starten. Solange noch kein Datenbankbefehl begonnen wurde, bleibt der automatische Image- und
Code-Rollback zulässig; erst ab dem tatsächlichen Start von Migration oder Seed wird ein reiner
Code-Rollback wegen möglicher Schema-Inkompatibilität konservativ gesperrt.

## Backup

```bash
sudo ./infrastructure/scripts/backup/backup-all.sh
```

Der produktive Lauf erzeugt **einen koordinierten Recovery-Punkt**. Wenn die API läuft, wird sie
standardmäßig kurz gestoppt, damit PostgreSQL und Laufzeitdateien dieselbe Anwendungsgrenze
abbilden. Danach entstehen ein PostgreSQL-Dump, das Dateiarchiv und optional das verschlüsselte
Recovery-Bundle. Die API wird unmittelbar wieder gestartet und auf Readiness geprüft.

Ein Lauf gilt erst als erfolgreich, wenn der frisch erzeugte Dump zusätzlich in eine isolierte
Staging-Datenbank importiert, mit dem aktuellen API-Image auf Alembic-Head migriert, hinsichtlich
der Verschlüsselungsschlüssel geprüft und durch einen echten API-Readiness-Test bestätigt wurde.
Der JSON-Nachweis wird zusammen mit allen Artefakten über Größe und SHA-256 in einem
Backup-Set-Manifest gebunden. Dieses Manifest ist der abschließende Commit-Marker.

Wichtige Verzeichnisse:

```text
infrastructure/data/backups/postgres/   Datenbankdumps und Restore-Metadaten
infrastructure/data/backups/files/      Laufzeitdateien
infrastructure/data/backups/recovery/   optionale age-Bundles
infrastructure/data/backups/reports/    vollständige Recovery-Preflight-Berichte
infrastructure/data/backups/sets/       atomare Backup-Set-Commit-Marker
```

`doctor.sh` bewertet Alter, Konsistenzmodus, Prüfsummen, Preflight-Bericht und Set-Manifest. Ein
unkoordinierter Live-Snapshot oder ein Dump ohne erfolgreichen Recovery-Nachweis wird nicht als
produktiver Wiederherstellungspunkt gemeldet. `BACKUP_RETENTION_DAYS` steuert die lokale Rotation;
mindestens eine unabhängige, vorzugsweise unveränderliche Offsite-Kopie bleibt erforderlich. Sobald die assistierte SFTP-Verbindung eingerichtet ist, veröffentlicht auch der tägliche systemd-Timer jedes erfolgreiche Set automatisch offsite; bei einem Übertragungsfehler bleibt der lokale Commit erhalten, der Timer-Lauf wird aber als fehlgeschlagen gemeldet.

Mit `BACKUP_RECOVERY_ENABLED=true` enthält derselbe koordinierte Lauf zusätzlich das
age-verschlüsselte Bare-Metal-Bundle. `BACKUP_AGE_RECIPIENT` darf ausschließlich den öffentlichen
Empfänger enthalten; der private Schlüssel bleibt auf dem externen Recovery-Gerät.

### Manuelle Recovery-Vorprüfung ohne Aktivierung

```bash
sudo ./infrastructure/scripts/backup/restore-postgres.sh \
  --preflight-only \
  --report /root/rbf-recovery-preflight.json \
  infrastructure/data/backups/postgres/<backup>.sql.gz
```

Dieser Modus verändert die aktive Datenbank nicht. Er importiert in Staging, prüft die
Alembic-Kompatibilität, führt ausschließlich Vorwärtsmigrationen aus, testet verschlüsselte Daten
und startet das aktuelle API-Image in einem internen Netz ohne veröffentlichte Ports.

### Assistierte Backup-Server-Einrichtung

Der empfohlene Ablauf tauscht nur öffentliche Enrollment-JSON-Dateien aus. Die Webseite erzeugt
den privaten SSH-Schlüssel selbst; das Recovery-Tool 1.4.1 richtet auf dem Backup-Server chroot-
isoliertes SFTP, Benutzer, Speicher, age-Identität und Retention ein. Nach dem Import der Antwort
werden Host-Key, SFTP und age-Empfänger automatisch geprüft beziehungsweise konfiguriert. Siehe
[Assistierte Backup-Server-Einrichtung](BACKUP_SERVER_ENROLLMENT.md).

### Remote-Anwendungsbackup aus dem Adminbereich

Administratoren können unter **Staff → Betrieb → Anwendungs-Backups** ein dediziertes
SSH-/SFTP-Ziel konfigurieren. Das Webinterface zeigt den tatsächlich vom Host verwendeten
öffentlichen Upload-Schlüssel und dessen Fingerprint an. Eine neue Konfiguration wird erst nach einem
vollständigen SFTP-Schreib-/Lese-/Löschtest gespeichert; der Test prüft damit Schlüssel, Host-Key,
Zielpfad und Schreibrechte gemeinsam. Der root-seitige Runner erzeugt anschließend denselben
koordinierten und vollständig verifizierten Backup-Punkt wie der Timer. Er überträgt Artefakte und
Prüfsummen atomar, verifiziert sie durch SFTP-Rückdownload, danach den Recovery-Bericht und
**zuletzt** das Backup-Set-Manifest als Remote-Commit-Marker. Ein Remote-Shellzugang ist nicht nötig.

Der geschützte Admin-Restore akzeptiert nur Datenbankdumps, die:

- gültige schema-2-Restore-Metadaten besitzen;
- als `application-quiesced` oder `no-running-api` gekennzeichnet sind;
- Mitglied eines lokal vollständig validierten Backup-Sets sind;
- mit dem aktiven Schlüsselring kompatibel sind.

Legacy-Backups oder bewusst unkoordinierte Snapshots bleiben ausschließlich über getrennte,
explizite Root-CLI-Ausnahmen erreichbar. Der Browser kann keine Dateipfade oder Ausnahmen vorgeben.

Status und Protokoll:

```text
infrastructure/data/control/status/backup-health.json
infrastructure/data/control/status/backup-status.json
infrastructure/data/control/status/backup.log
```

Das verbindliche externe Pull- und Bare-Metal-Verfahren steht in
[`docs/DISASTER_RECOVERY.md`](DISASTER_RECOVERY.md).

## Discord-Webhook-Schlüssel

`infrastructure/.env` enthält `WEBHOOK_ENCRYPTION_KEYS`. Der erste, kommagetrennte
Fernet-Schlüssel verschlüsselt neue Discord-Webhook-Tokens; nachfolgende Schlüssel dienen der
Entschlüsselung während einer Rotation. Der Updater erzeugt den Schlüssel bei alten Installationen
automatisch. Die Datei bleibt mit Modus `0600` geschützt und muss getrennt vom Datenbankbackup
gesichert werden.

Rotation in einem Wartungsfenster:

1. neuen Schlüssel erzeugen und vor die bestehende Liste setzen;
2. API neu starten und den Maintenance-Start abwarten;
3. alle Webhooks testen und ein neues Datenbankbackup erstellen;
4. erst danach alte Schlüssel aus der Liste entfernen.

Ein Datenbankbackup ohne mindestens einen gültigen Schlüssel kann die gespeicherten Discord-Ziele
nicht wiederherstellen.

Build-Printouts verwenden die vorhandenen, verschlüsselt gespeicherten Discord-Ziele. In der
Webhook-Verwaltung kann dafür das Ereignis `build.printout.published` zusätzlich zu
`build.created`, `build.updated` und `build.removed` abonniert werden. Die Build-Ansicht rendert
das PNG im Browser, speichert serverseitig pro Build genau eine öffentliche Datei und übergibt
Discord deren URL als Bild-Embed. Der SHA-256-Wert verhindert unnötige Neuschreibvorgänge;
nach einer Build-Bearbeitung ersetzt das neu gerenderte Bild den bisherigen Inhalt unter derselben
URL.

## Monitoring-Major-Upgrade

Uptime Kuma bleibt bis zur kontrollierten Datenmigration auf 1.23.16. Das verbindliche Verfahren
für Backup, Migration, Verifikation und Rollback steht in `docs/UPTIME_KUMA_2_MIGRATION.md`. Die
Image-Version darf nicht im Rahmen eines normalen unbeaufsichtigten App-Updates auf 2.x geändert
werden.

## Automatische Datenbereinigung

Der Maintenance-Lauf entfernt abgelaufene Sessions und wendet die in `backend/config/uploads.cfg`
konfigurierten Fristen auf Sicherheitsaggregationen, Audit-Historie, Webhook-Deliveries,
Cookie-Einwilligungen, Registrierungsanträge sowie abgeschlossene Datenschutzanträge und
-kontakte an. Die Standardwerte und betrieblichen Auswirkungen sind in
[DATA_RETENTION.md](DATA_RETENTION.md) dokumentiert. Nach Änderungen an Fristen sollte der nächste
Lauf beobachtet und das Ergebnis über die Systemlogs geprüft werden.

## Datenschutzvorgänge

Die öffentliche Seite `/privacy` bietet Cookie-Einstellungen, den Self-Service für angemeldete
Nutzer und ein datensparsames Kontaktformular. Administratoren bearbeiten formale Anträge und
Kontakte unter `/admin/privacy-requests`. Vor einer Löschfreigabe sind Identität, gesetzliche
Aufbewahrungspflichten und mögliche Rechte an Community-Inhalten zu prüfen; die anschließende
relationale Bereinigung, Pseudonymisierung und der Sessionwiderruf laufen automatisiert.

Datenschutzkontakte dürfen nicht in Discord kopiert werden. Die Anwendung versendet deren Adresse,
Betreff und Nachricht bewusst nicht über Webhooks. Nach einer Test- oder Fehlanfrage ist sie über
die Admin-Inbox abzuschließen; der tägliche Maintenance-Lauf entfernt abgeschlossene Vorgänge nach
der dokumentierten Frist. Der vollständige technische und organisatorische Prüfstand steht in
[PRIVACY_COMPLIANCE_AUDIT.md](PRIVACY_COMPLIANCE_AUDIT.md).

## TLS

```bash
./infrastructure/scripts/tls/renew-certificate.sh
./infrastructure/scripts/tls/sync-certificate.sh
```

systemd-Timer übernehmen Erneuerung und Backups. Änderungen an `.env` mit `chmod 600` schützen und
nie in Git aufnehmen.


## New-Captain-Guide pflegen

Staff-Mitglieder können Textabschnitte, Ressourcensammlungen sowie direkte Guide- und Build-Links
ergänzen. Veröffentlichte Guides und verfügbare Builds werden beim Öffnen des Editors geladen.
Verknüpfungen bleiben Datenbankreferenzen, sodass umbenannte Inhalte automatisch ihren aktuellen
Titel anzeigen.


### Automatisch getrennter Recovery-Lesezugang

Das Server-Provisioning erzeugt neben dem schreibenden Produktiv-Uploadkonto einen zweiten, nur lokal erreichbaren und durch `internal-sftp -R` read-only erzwungenen Recovery-Zugang. Der zugehörige private SSH-Schlüssel und die private age-Identität verbleiben auf dem Backup-/Recovery-Gerät. Das Tool testet diesen Zugang und speichert automatisch ein lokales Pull-Profil; anschließend genügt `rbf-recovery-tool pull`.
