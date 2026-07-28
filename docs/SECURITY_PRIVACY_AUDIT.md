# Security- und Datenschutz-Audit — 28. Juli 2026

## Umfang und Methode

Geprüft wurden Anwendungscode, API-Schemas, Authentifizierung, Berechtigungen, Uploads, Discord-
Integrationen, Logging, Backups, Container-/NGINX-Konfiguration, CI und Datenaufbewahrung. Die Prüfung
war eine statische Code- und Konfigurationsanalyse mit Regressionstests; sie ersetzt keinen externen
Penetrationstest, keine Datenschutz-Rechtsberatung und keinen Test der produktiven Netzwerkumgebung.

## Ergebnis

Es wurde keine unmittelbar ausnutzbare kritische Schwachstelle im geprüften Stand gefunden. Die
vorhandene Sicherheitsbasis ist stark: serverseitige Sessions, sichere Cookies, Origin-Prüfung,
rollenbasierte Endpunkte, nicht privilegierte Container, interne Datenbankzone, Upload-Magic-Byte-
Prüfung, SSRF-geschützte Discord-Zustellung, striktes SSH-Host-Key-Pinning und root-seitige Control-
Runner ohne Docker-Socket im Webprozess.

Im Frühjahrsputz wurden folgende Risiken direkt reduziert:

- eingebettete Autoren-/Owner-Objekte liefern nur noch `id` und Anzeigenamen;
- geprüfte Registrierungs-Passworthashes werden sofort entfernt;
- Query-Werte und rohe Proxy-Ketten werden nicht mehr persistiert;
- blockierte IP-Adressen werden nicht im 403-Response gespiegelt;
- Retention für Webhook-Historie, Cookie-Entscheidungen und Registrierungsanträge ist erzwungen;
- mutable Schema-Defaults wurden entfernt;
- die CSS-/Repository-Gates sind deterministisch und verhindern neue Monolithen.

## Offene Befunde

### Hoch — Discord-Webhook-Tokens liegen in der Datenbank im Klartext

Discord-Webhook-URLs enthalten ein schreibberechtigendes Token. API-Antworten maskieren es und die
Datenbank ist intern, bei einem Datenbankabzug wären die Tokens jedoch nutzbar. Empfohlen wird eine
Anwendungsverschlüsselung mit einem außerhalb der Datenbank gespeicherten Schlüssel, versioniertem
Ciphertext, Rotationspfad und Migration. Bis dahin: Datenbank-/Backup-Zugriff streng begrenzen und
Tokens nach einem Verdacht sofort in Discord rotieren.

### Hoch — Öffentliche Datenschutzerklärung und Verantwortlichenangaben sind nicht als Route enthalten

Die Anwendung bietet Cookie-Einstellungen, aber keine repositoryseitige Datenschutzerklärung oder
Impressumsseite. Vor dem Produktivbetrieb müssen Verantwortlicher, Kontakt, Zwecke, Rechtsgrundlagen,
Empfänger, Drittlandtransfers, Fristen und Betroffenenrechte in einer geprüften öffentlichen Fassung
bereitgestellt und im Footer verlinkt werden. Inhalte dürfen nicht automatisch erfunden werden.

### Mittel — Kein Self-Service für Auskunft, Export und Kontolöschung

Administratoren können Inhalte moderieren, es gibt aber keinen zusammenhängenden Betroffenenworkflow.
Empfohlen sind ein maschinenlesbarer Export, ein dokumentierter Lösch-/Anonymisierungsplan für
referenzierte Inhalte und ein Admin-Workflow mit Vier-Augen- oder Bestätigungsstufe. Bis dahin ist ein
manueller Prozess mit Identitätsprüfung, Fristverfolgung und Audit-Eintrag erforderlich.

### Mittel — Remote-Backups sind transportverschlüsselt, aber nicht anwendungsseitig verschlüsselt

SFTP und Host-Key-Pinning schützen die Übertragung. Der Dump liegt auf dem Zielserver als lesbares
Archiv, sofern dessen Datenträger nicht separat verschlüsselt ist. Empfohlen sind verschlüsselte
Zieldatenträger oder eine clientseitige Archivverschlüsselung mit getrennt verwaltetem Schlüssel und
regelmäßigem Restore-Test.

### Mittel — Discord kann personenbezogene Inhalte als externer Empfänger erhalten

Automations- und Broadcast-Templates können Anzeigenamen, Flottenvorgänge oder redaktionelle Inhalte
enthalten. Eventauswahl und Templates sollten nach Datenminimierung geprüft werden. Verantwortliche
müssen Rechtsgrundlage, Empfängerinformation, Auftrags-/Drittlandthemen und Löschbarkeit auf Discord
organisatorisch klären. Keine Zugangsdaten, internen Notizen oder vollständigen Profile in Templates.

### Mittel — Sicherheitslogs enthalten IP-Adresse und User-Agent

Diese Daten sind für Missbrauchserkennung nachvollziehbar, können aber personenbezogen sein. Die neue
30-Tage-Frist und Query-Redaktion reduzieren das Risiko. Produktionsdokumentation sollte Zweck,
Rechtsgrundlage, Zugriffskreis und Löschfrist ausdrücklich nennen; eine noch kürzere Frist ist zu
prüfen.

### Niedrig — CSP benötigt weiterhin `style-src 'unsafe-inline'`

Vue nutzt an mehreren Stellen dynamische Inline-Styles für Fortschritts-/Balkendarstellungen. Skripte
sind bereits auf `'self'` beschränkt und Markdown wird ohne HTML gerendert und mit DOMPurify
bereinigt. Langfristig können dynamische Werte über streng validierte CSS-Custom-Properties oder
klassenbasierte Stufen migriert werden, um `unsafe-inline` für Styles zu entfernen.

### Niedrig — Automatisierter Vulnerability-Scan ist nicht Teil des lokalen Gates

Dependabot deckt pip, npm, Actions und Docker ab. Zusätzlich empfohlen sind GitHub Dependency Review
für Pull Requests und ein geplanter OSV-/SBOM-Scan. Solche Netzwerkprüfungen sollten bewusst als
separater CI-Job mit klarer Verfügbarkeits- und Schweregradpolitik eingerichtet werden, damit ein
externer Advisory-Ausfall nicht die deterministischen Unit-Tests verfälscht.

## Datenschutz-Datenfluss

| Quelle | Daten | Ziel / Empfänger | Schutz |
|---|---|---|---|
| Anmeldung | Benutzername, Passworthash, Session | PostgreSQL, Browser-Cookie | PBKDF2, serverseitiges Token-Hashing, HttpOnly/Secure/SameSite |
| Registrierung | Profilkern, optionaler Flottenantrag | Staff-Prüfung, PostgreSQL | Rollenprüfung, Hashentfernung nach Review, Retention |
| Request-Telemetrie | IP, User-Agent, Route, Status | Admin-Systemlogs | Admin-only, Query-Redaktion, 30 Tage |
| Inhalte/Uploads | Beiträge, Guides, Builds, Dateien | angemeldete oder fachlich öffentliche Nutzer | MIME/Magic-Byte/Quota, Zugriffsendpunkt |
| Discord | ausgewählte Event-/Broadcast-Inhalte | konfigurierte Discord-Server | SSRF-Schutz, URL-Maskierung, Delivery-Retention |
| Backup | vollständiger PostgreSQL-Dump | konfigurierter Backup-Server | root-Runner, SFTP, Host-Key-Pinning, Prüfsumme |

## Priorisierte nächste Schritte

1. Rechtlich geprüfte Datenschutz-/Impressumsseiten bereitstellen und Footer-Verknüpfung ergänzen.
2. Discord-Webhook-Secrets anwendungsseitig verschlüsseln und rotierbar machen.
3. Export-/Löschworkflow für Betroffenenanfragen konzipieren und testen.
4. Remote-Backup-Verschlüsselung und regelmäßigen Restore-Nachweis ergänzen.
5. Dependency Review und geplanten OSV-/SBOM-Scan als separaten Security-Workflow etablieren.
6. Externe Penetrationstests gegen die produktive Domain und das Backup-Ziel durchführen.

## Referenzrahmen

Die Bewertung orientiert sich an DSGVO-Grundsätzen wie Zweckbindung, Datenminimierung, Speicherbegrenzung,
Integrität/Vertraulichkeit und Rechenschaftspflicht, an EDPB-Leitlinien zu Datenschutz durch Technikgestaltung
und datenschutzfreundliche Voreinstellungen sowie an OWASP-Empfehlungen zu sicherem Logging, CSP, XSS und
Session-Management.

## Technische Verifikation dieses Stands

- 170 Backend-Tests in 41 isolierten Testmodulen bestanden.
- 81 dependency-freie Frontend-Tests bestanden; der einzelne Guide-Export-Test benötigt das in der Analyseumgebung nicht installierbare Paket `dompurify`.
- Repository-, CSS-, Infrastruktur-, Shell-, Python-AST- und Workflow-YAML-Prüfungen bestanden.
- Statische Suche nach eingebetteten privaten Schlüsseln, Discord-Webhook-Credentials und hochentropischen Secret-Literalen ergab nach manueller False-Positive-Prüfung keinen Fund.
- Der vollständige npm-/Vite-Lauf konnte nicht ausgeführt werden, weil der interne Paketspiegel beim Abruf von `vue-router`, `vite` und weiteren Paketen HTTP 503 lieferte.

Die Befunde beruhen auf dem Repository-Stand und simulierten Infrastrukturpfaden. Produktive DNS-, TLS-, Firewall-, Backup-Ziel- und Discord-Konfigurationen müssen separat geprüft werden.
