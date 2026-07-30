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

### Teilweise behoben — Öffentliche Anbieterkennzeichnung vorhanden, Datenschutztext weiter offen

Die Anwendung besitzt nun eine öffentliche, im Footer verlinkte Impressumsseite mit Entwurfsmodus.
Auslieferungsdefaults kommen aus `LEGAL_NOTICE_*`; nach einer Bearbeitung im admin-exklusiven
Staff-Panel bleibt die persistierte Fassung maßgeblich. Unveröffentlichte Entwurfsangaben werden
nicht über die öffentliche API ausgegeben. Die Anwendung entscheidet jedoch nicht automatisch, ob
für den konkreten Betreiber bereits eine Pflicht nach § 18 MStV, § 5 DDG oder weiteren Vorschriften
besteht, und ersetzt keine rechtliche Prüfung. Eine rechtlich geprüfte Datenschutzerklärung mit
Verantwortlichem, Zwecken, Rechtsgrundlagen, Empfängern, Drittlandtransfers, Aufbewahrungsfristen
und Betroffenenrechten fehlt weiterhin und bleibt ein Go-live-Punkt.

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

### Behoben — Zweckgebundene IP-Sperrsignale statt Request-Logs

Die allgemeine persistente Request-Telemetrie wurde entfernt. Die Anwendung speichert nur noch
IP-Adresse, UTC-Kalendertag, Tageszähler und eine grobe bannrelevante Kategorie (Scan,
Login-Fehlschlag oder Rate-Limit). Einzelne Request-Zeitpunkte werden nicht gespeichert. Route, Query-String, User-Agent, Request-ID, Inhalte, Statusdetails und Exceptions werden
nicht in der Datenbank gespeichert und nicht über die Admin-Webseite bereitgestellt. Signale werden
nach sieben Tagen oder unmittelbar beim Sperren der IP gelöscht. NGINX-Access-Logs sind deaktiviert.
Die konkrete Rechtsgrundlage, Empfängerkreis und Löschfrist müssen weiterhin in der
Datenschutzerklärung des Betreibers genannt werden.

## Datenschutz-Datenfluss

| Quelle | Daten | Ziel / Empfänger | Schutz |
|---|---|---|---|
| Anmeldung | Benutzername, Passworthash, Session | PostgreSQL, Browser-Cookie | PBKDF2, serverseitiges Token-Hashing, HttpOnly/Secure/SameSite |
| Registrierung | Profilkern, optionaler Flottenantrag | Staff, PostgreSQL | Rollenprüfung, Hashentfernung nach Review, Retention |
| IP-Sperrsignale | IP, UTC-Tag, grobe Signalkategorie, Tageszähler | Admin-Sperrkandidaten | Admin-only, Tagesaggregation, 7-Kalendertage-Retention, Sofortlöschung bei Sperre |
| Inhalte/Uploads | Beiträge, Guides, Builds, Dateien | fachlich berechtigte Nutzer | MIME-/Magic-Byte-Prüfung, Quota, Zugriffsendpunkt |
| Discord | ausgewählte Event-/Broadcast-Inhalte | konfigurierte Discord-Server | Ziel-Allowlist, verschlüsselte Tokens, Maskierung, Delivery-Retention |
| Backup | vollständiger PostgreSQL-Dump | Backup-Server | root-Runner, SFTP, Host-Key-Pinning, SHA-256 |

## Priorisierte nächste Schritte

1. Impressumsentwurf rechtlich prüfen/veröffentlichen und eine vollständige Datenschutzerklärung bereitstellen.
2. Uptime-Kuma-2-Migration nach dem neuen Runbook in einem Wartungsfenster durchführen.
3. Image-Scan und Release-SBOM ergänzen.
4. Export-/Löschworkflow für Betroffenenanfragen umsetzen.
5. Remote-Backup-Verschlüsselung und Restore-Nachweis ergänzen.
6. Externen Penetrationstest gegen Produktivdomain, API und Backup-Ziel durchführen.

## Verifikation

Für diesen Stand wurden erfolgreich ausgeführt:

- 197 Backendtests aus allen 46 Testmodulen;
- Alembic Upgrade/Check/Downgrade/Upgrade einschließlich absichtlicher Löschung der bisherigen
  `app_logs`-Daten beim Wechsel auf tägliche IP-Sperrsignale;
- 99 von 100 direkt gestarteten Frontend-Unit-Tests sowie alle 18 unmittelbar betroffenen
  Datenschutz-/Staff-UI-Regressionstests;
- Locale-Vollständigkeitsprüfung mit 2.059 Schlüsseln pro Sprache und ohne fehlende oder
  englische Fallback-Texte in allen sieben unterstützten Sprachen;
- 6.932 deterministische Offline-Sicherheitsinvarianten sowie Repository-, CSS-, Workflow-YAML-, Shell- und Infrastrukturprüfungen.

Der einzige nicht ausführbare Frontend-Test ist der Guide-Export-Test, weil das im Repository-Archiv
nicht installierte Paket `dompurify` in der Analyseumgebung fehlt. Ein vollständiger npm-/Vite-Build
konnte deshalb ohne erfolgreiches `npm ci` nicht reproduziert werden; die direkt betroffenen
Frontendtests sind grün.

Reproduzierbare Einstiegspunkte:

```bash
make security-audit
make test
make test-full
```

Die Bewertung gilt für den Repository-Stand. Produktive DNS-, TLS-, Firewall-, Reverse-Proxy-,
Backup- und Discord-Konfigurationen müssen separat geprüft werden.
