# Security- und Datenschutz-Audit — 28. Juli 2026

## Umfang und Methode

Geprüft wurden Backend und Frontend, Authentifizierung und Autorisierung, Uploads, ausgehende
Discord-Webhooks, Datenhaltung und Retention, Alembic-Migrationen, NGINX/TLS-Header, Docker Compose,
Host-Runner, Backups sowie GitHub Actions. Die Prüfung kombiniert manuelle Code- und
Konfigurationsanalyse, offline ausführbare Sicherheitsinvarianten und Regressionstests.

Nicht Bestandteil waren ein externer Penetrationstest, eine rechtliche Datenschutzprüfung, ein
Produktions-Firewall-/DNS-Audit oder ein authentifizierter Scan des laufenden Servers. Online-
Advisory-Datenbanken konnten in der isolierten Analyseumgebung nicht vollständig abgefragt werden;
für diesen Zweck wurde ein eigener OSV-Workflow in CI ergänzt.

## Gesamtergebnis

Im geprüften Anwendungscode wurde keine unmittelbar ausnutzbare kritische Schwachstelle gefunden.
Die technische Basis ist überdurchschnittlich solide: serverseitige Sessions, sichere Cookies,
Origin-Prüfung, rollenbasierte Endpunkte, Upload-Prüfung anhand echter Dateisignaturen,
SSRF-begrenzte Discord-Ziele, interne Datenbankzone, read-only Anwendungscontainer,
`no-new-privileges`, striktes SSH-Host-Key-Pinning und kein Docker-Socket im Webprozess.

Der Frühjahrsputz hat folgende Befunde direkt geschlossen oder reduziert:

- Discord-Webhook-URLs werden vor der Persistierung authentifiziert verschlüsselt; Klartextbestände
  werden beim Maintenance-Start migriert und alte Schlüssel kontrolliert auf den Primärschlüssel
  rotiert. Nach der Entschlüsselung wird das Ziel unmittelbar vor der Zustellung erneut gegen die
  Discord-Allowlist geprüft.
- Ein separater `WEBHOOK_ENCRYPTION_KEYS`-Schlüssel wird von Setup/Updater erzeugt und bleibt
  außerhalb der Datenbank. Bestehende Installationen besitzen einen rückwärtskompatiblen
  Übergangspfad.
- Das veraltete frei konfigurierbare Discord-Avatar-Feld wurde aus API, Modell und Schema entfernt;
  Webhooks verwenden ausschließlich das öffentliche Flotten-Icon.
- OSV-Scans laufen für Pull Requests, Merge-Gruppen, Pushes auf `main` und wöchentlich; die lokalen
  Repository-Gates prüfen zusätzlich projektbezogene Sicherheitsinvarianten ohne Netzwerk.
- Alle externen GitHub Actions wurden auf geprüfte vollständige Commit-SHAs festgeschrieben;
  persistierte Checkout-Credentials sind in Build-/Testjobs deaktiviert.
- Migrations- und Seed-Container laufen read-only mit temporärem `/tmp`.
- NGINX liefert zusätzliche COOP-, CORP- und Cross-Domain-Policy-Header aus.
- Tote Avatar-Kompatibilitätsfelder, generierte Caches und inkonsistente Sicherheitsdokumentation
  wurden entfernt beziehungsweise aktualisiert.

## Geschlossene Befunde

### Discord-Webhook-Tokens im Klartext — geschlossen

`endpoint_url` bleibt aus Kompatibilitätsgründen der Spaltenname, enthält jedoch nur noch versionierte
Fernet-Ciphertexte. API-Antworten maskieren zusätzlich die URL. Der erste konfigurierte Schlüssel
verschlüsselt; weitere Schlüssel dienen zur Entschlüsselung und Rotation. Manipulierte Ciphertexte
und verschlüsselte Nicht-Discord-Ziele werden abgewiesen und nicht an den Transport weitergereicht.

### Fehlender automatisierter Dependency-Scan — geschlossen

`.github/workflows/security.yml` führt OSV gegen npm- und Python-Lockfiles aus. Pull Requests werden
auf neu eingeführte Schwachstellen geprüft; vollständige Scans laufen auf `main`, manuell und nach
Zeitplan. Der Scan bleibt bewusst vom deterministischen Offline-Testlauf getrennt.

## Offene Befunde

### Hoch — Rechtstexte und Verantwortlichenangaben fehlen als öffentliche Route

Die Anwendung besitzt Cookie-Einstellungen, aber keine repositoryseitig geprüfte Datenschutz- oder
Impressumsseite. Vor öffentlicher Nutzung müssen Verantwortlicher, Kontakt, Zwecke,
Rechtsgrundlagen, Empfänger, Drittlandtransfers, Aufbewahrungsfristen und Betroffenenrechte in einer
rechtlich geprüften Fassung bereitgestellt und im Footer verlinkt werden. Diese Inhalte dürfen nicht
automatisch erfunden werden.

### Hoch — Uptime Kuma 1.23.16 benötigt eine geplante Major-Migration

Das optionale Monitoring ist weiterhin auf `louislam/uptime-kuma:1.23.16` festgeschrieben, während
die aktuelle Produktlinie Version 2 ist. Ein automatisches Tag-Update wurde bewusst nicht eingebaut:
die 1→2-Migration verändert die Heartbeat-Datenhaltung, kann auf langsamer Hardware lange dauern und
darf nicht unterbrochen werden. Vor der Umstellung sind zwei geprüfte Kopien von
`infrastructure/data/uptime-kuma`, ein Wartungsfenster und ein dokumentierter Rollback erforderlich.

### Mittel — Kein Self-Service für Auskunft, Export und Kontolöschung

Es gibt keinen zusammenhängenden Betroffenenworkflow. Empfohlen sind ein maschinenlesbarer Export,
ein dokumentierter Lösch-/Anonymisierungsplan für referenzierte Inhalte und ein bestätigter
Admin-Workflow mit Audit-Eintrag. Bis dahin ist ein manueller Prozess mit Identitätsprüfung und
Fristverfolgung erforderlich.

### Mittel — Remote-Backups sind nicht anwendungsseitig verschlüsselt

SFTP und Host-Key-Pinning schützen die Übertragung. Der PostgreSQL-Dump ist auf dem Ziel lesbar,
sofern dessen Datenträger nicht separat verschlüsselt ist. Empfohlen sind verschlüsselte
Zieldatenträger oder clientseitige Archivverschlüsselung mit getrenntem Schlüssel und regelmäßigem
Restore-Test.

### Mittel — Discord ist ein externer Datenempfänger

Event- und Broadcast-Templates können Anzeigenamen, Flottenvorgänge oder redaktionelle Inhalte
übertragen. Eventauswahl und Templates müssen nach Datenminimierung geprüft werden. Keine
Zugangsdaten, internen Notizen oder vollständigen Profile in Templates aufnehmen.

### Mittel — Produktionsimages benötigen einen regelmäßigen Image-/SBOM-Scan

Die Images sind reproduzierbar versioniert, aber ein Lockfile-Scan erfasst keine Schwachstellen in
Alpine-/Debian-Systempaketen. Insbesondere der Gateway-Pin `nginx:1.27.5-alpine3.21` liegt hinter
den aktuellen offiziellen Release-Linien und benötigt einen getesteten Refresh. Ein automatischer
Sprung wurde ohne Image-Build und produktionsnahen Smoke-Test bewusst nicht vorgenommen. Empfohlen
sind ein separater Trivy-, Grype- oder vergleichbarer Image-Scan nach dem Build sowie eine
versionierte SBOM für Releases. Schweregrad- und Ausnahmeregeln müssen vor Aktivierung festgelegt
werden.

### Niedrig — CSP benötigt weiterhin `style-src 'unsafe-inline'`

Skripte sind auf `'self'` beschränkt; dynamische Vue-Styles erfordern jedoch weiterhin Inline-Styles.
Langfristig sollten dynamische Werte über validierte CSS-Custom-Properties oder Klassenstufen
abgebildet werden.

### Niedrig — Sicherheitslogs enthalten IP-Adresse und User-Agent

Diese Daten sind für Missbrauchserkennung nachvollziehbar, können aber personenbezogen sein. Die
bestehende Retention und Query-Redaktion reduzieren das Risiko. Zweck, Rechtsgrundlage,
Zugriffskreis und Löschfrist müssen in der Datenschutzerklärung genannt werden.

## Datenschutz-Datenfluss

| Quelle | Daten | Ziel / Empfänger | Schutz |
|---|---|---|---|
| Anmeldung | Benutzername, Passworthash, Session | PostgreSQL, Browser-Cookie | PBKDF2, serverseitiges Token-Hashing, HttpOnly/Secure/SameSite |
| Registrierung | Profilkern, optionaler Flottenantrag | Staff, PostgreSQL | Rollenprüfung, Hashentfernung nach Review, Retention |
| Request-Telemetrie | IP, User-Agent, Route, Status | Admin-Systemlogs | Admin-only, Query-Redaktion, Retention |
| Inhalte/Uploads | Beiträge, Guides, Builds, Dateien | fachlich berechtigte Nutzer | MIME-/Magic-Byte-Prüfung, Quota, Zugriffsendpunkt |
| Discord | ausgewählte Event-/Broadcast-Inhalte | konfigurierte Discord-Server | Ziel-Allowlist, verschlüsselte Tokens, Maskierung, Delivery-Retention |
| Backup | vollständiger PostgreSQL-Dump | Backup-Server | root-Runner, SFTP, Host-Key-Pinning, SHA-256 |

## Priorisierte nächste Schritte

1. Rechtlich geprüfte Datenschutz-/Impressumsseiten bereitstellen.
2. Uptime-Kuma-2-Migration nach dem neuen Runbook in einem Wartungsfenster durchführen.
3. Image-Scan und Release-SBOM ergänzen.
4. Export-/Löschworkflow für Betroffenenanfragen umsetzen.
5. Remote-Backup-Verschlüsselung und Restore-Nachweis ergänzen.
6. Externen Penetrationstest gegen Produktivdomain, API und Backup-Ziel durchführen.

## Verifikation

Für diesen Stand wurden erfolgreich ausgeführt:

- 7.027 deterministische Offline-Sicherheitsinvarianten;
- Repository-, CSS-, Workflow-YAML-, Shell- und Infrastrukturprüfungen;
- Alembic Upgrade/Check/Downgrade/Upgrade auf einer temporären Datenbank;
- 44 direkt betroffene Backend-Regressionstests für Webhooks, Verschlüsselung, Konfiguration,
  Retention und Sicherheitsgrenzen sowie 29 angrenzende Build-Regeltests;
- 99 von 100 direkt gestarteten Frontend-Unit-Tests. Der verbleibende Guide-Export-Test benötigt
  das in der Analyseumgebung nicht installierte Paket `dompurify`.

Der vollständige Backend-Sammellauf und der npm-/Vite-Build konnten in der Sandbox nicht vollständig
abgeschlossen werden: der Backend-Sammellauf überschritt das Ausführungszeitfenster, und es waren
keine installierten npm-Abhängigkeiten beziehungsweise kein Paketnetz verfügbar. Die isolierten,
direkt betroffenen Module sind grün; die neu ergänzten CI-Jobs führen die vollständigen Online- und
Build-Prüfungen im Repository aus.

Reproduzierbare Einstiegspunkte:

```bash
make security-audit
make test
make test-full
```

Die Bewertung gilt für den Repository-Stand. Produktive DNS-, TLS-, Firewall-, Reverse-Proxy-,
Backup- und Discord-Konfigurationen müssen separat geprüft werden.
