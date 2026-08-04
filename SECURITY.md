# Sicherheitsrichtlinie

## Unterstützte Version

Nur die aktuelle v1.x-Linie erhält Sicherheitskorrekturen.

## Meldung

Sicherheitsprobleme bitte nicht öffentlich als Issue veröffentlichen. Nutze GitHub Private
Vulnerability Reporting oder kontaktiere den Repository-Betreiber direkt. Beschreibe betroffene
Version, Reproduktionsschritte, Auswirkung und einen möglichen Fix.

## Produktionsgrundsätze

- `.env`, Zugangsdaten, Datenbanken, Uploads und Backups werden nie eingecheckt.
- PostgreSQL ist nur an Loopback gebunden; die API ist ausschließlich über NGINX erreichbar.
- API und Migrationscontainer laufen als unprivilegierter Benutzer und ohne Docker-Socket.
- Admin-Updates akzeptieren nur zwei fest definierte Operationen; Browserdaten werden nicht als
  Shell-Argumente ausgeführt.
- GitHub Actions besitzen standardmäßig nur Leserechte. Produktion nutzt ein geschütztes
  `production`-Environment und einen dedizierten SSH-Schlüssel.
- Die Host-Administration kann über einen separaten, schlüsselgebundenen
  `rbfadmin`-Account erfolgen. Dieser Account ist von den privaten
  Anwendungsaccounts getrennt, besitzt keinen Docker-Gruppenzugriff und
  deaktiviert Passwort-, Agent- und Forwarding-Zugriffe konto-spezifisch.
- Vor Migration oder Seed erstellt der Updater ein vollständiges Sicherheitsbackup.
- Manuelle Remote-Backups verwenden einen separaten root-seitigen systemd-Runner. Die API besitzt weder Docker-Socket- noch Lesezugriff auf den privaten Backup-Schlüssel; SSH-Host-Keys werden vor jeder Verbindung strikt aus einer dedizierten `known_hosts`-Datei geprüft.
- Lokale PostgreSQL-Restores akzeptieren keine Browserpfade oder freien Dateinamen. Der Host katalogisiert nur reguläre, SHA-256-verifizierte Dumps; ein Restore erfordert den Bootstrap-Admin, eine exakte Bestätigung und einen einmaligen per `sudo` erzeugten Host-Token. Der Klartext-Token wird nicht in der Warteschlange, API-Antwort oder im Audit-Log persistiert. Kurzlebige Restore-Freigaben werden außerdem ausdrücklich aus Recovery-Bundles ausgeschlossen.
- Das eingefrorene Recovery-Tool für Windows und Linux baut auf einer gemeinsamen Codebasis auf, pinnt SSH-Host-Keys, speichert keine Kennwörter und prüft Transport-SHA-256, age-Entschlüsselung, Archivstruktur, Manifestinventar sowie jede enthaltene Datei. Es öffnet keine eingehenden Ports und benötigt keine Firewall-Freigabe auf dem Backup-Laptop.

Secrets nach einem Verdacht sofort rotieren: PostgreSQL, Seed-Admin,
`WEBHOOK_ENCRYPTION_KEYS`, Discord-Webhooks, SSH-Deploy-Key und gegebenenfalls TLS-Zugangsdaten.

## Secret-Rotation

`setup.sh --regenerate-secrets` ist nur für eine noch nicht initialisierte Installation vorgesehen.
Bei einer bestehenden PostgreSQL-Instanz werden Datenbankrolle, `.env` und abhängige Dienste in
einem geplanten Wartungsfenster gemeinsam rotiert; ein bloßes Überschreiben der `.env` ist verboten.
Discord-Webhook-Schlüssel werden als kommagetrennte Key-Ring-Liste rotiert: neuen Schlüssel zuerst
eintragen, Maintenance-Reverschlüsselung und Webhook-Tests abwarten, Backup erstellen und erst dann
alte Schlüssel entfernen.


## Datenschutz und Aufbewahrung

Datenminimierung und Löschfristen sind Sicherheitsanforderungen. Die technisch erzwungenen Fristen
stehen in `docs/reference/DATA_RETENTION.md`; offene Befunde und Verantwortlichkeiten stehen in
`docs/development/QUALITY_STANDARDS.md` und `docs/reference/DATA_RETENTION.md`.
Query-Werte, Proxy-Ketten und geprüfte Registrierungsgeheimnisse
dürfen nicht dauerhaft gespeichert werden. Änderungen an Datenflüssen, Logging, Drittanbietern oder
Backups benötigen eine erneute Datenschutzprüfung.
