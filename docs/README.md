# Projektdokumentation

Dieser Index ist der verbindliche Einstieg. Betriebsanweisungen und Standards beschreiben den
aktuellen Sollzustand; Dateien mit `AUDIT`, `ANALYSIS` oder `REVIEW` im Namen sind nachvollziehbare
Momentaufnahmen und ersetzen nicht das jeweils führende Dokument.

## Schnellzugriff

- Entwickeln: [DEVELOPMENT.md](DEVELOPMENT.md) und [TESTING.md](TESTING.md)
- Installieren: [INSTALLATION.md](INSTALLATION.md) und [GO_LIVE.md](GO_LIVE.md)
- Betreiben: [OPERATIONS.md](OPERATIONS.md) und [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md)
- Datenschutz: [PRIVACY_COMPLIANCE_AUDIT.md](PRIVACY_COMPLIANCE_AUDIT.md) und [DATA_RETENTION.md](DATA_RETENTION.md)
- Qualität: [QUALITY_STANDARDS.md](QUALITY_STANDARDS.md) und [ARCHITECTURE.md](ARCHITECTURE.md)

## Verbindliche Standards

- [Qualitätsstandards](QUALITY_STANDARDS.md) – zentraler Qualitätsvertrag und Definition of Done
- [Architektur](ARCHITECTURE.md) – Systemgrenzen und Modulregeln
- [Frontend- und CSS-Architektur](CSS_ARCHITECTURE.md) – Design, Responsive-Verhalten und CSS-Budgets
- [Backup-Architektur](BACKUP_ARCHITECTURE.md) – Backup, Enrollment und Recovery Tool
- [Tests](TESTING.md) – Testpyramide und Release-Gates
- [Datenbank](DATABASE.md) – 3NF, Alembic, Seeds und Backups
- [Security- und Datenschutz-Audit](SECURITY_PRIVACY_AUDIT.md) – Risiken und Administrator-Gates
- [Dreifachprüfung Datenschutz-Compliance](PRIVACY_COMPLIANCE_AUDIT.md) – Cookies, Datenflüsse und Löschworkflow
- [Docker- und Container-Sicherheit](CONTAINER_SECURITY.md) – Runtime-, Image- und Incident-Standard
- [Repository-Qualitätsaudit August 2026](QUALITY_AUDIT_2026-08.md) – aktueller Erfüllungsstand

## Entwicklung und Lieferung

- [Lokale Entwicklung](DEVELOPMENT.md)
- [Repository-Aufräumstandard](REPOSITORY_CLEANUP.md)
- [Deployment und CI/CD](DEPLOYMENT.md)
- [Go-Live-Checkliste](GO_LIVE.md)

## Installation und Betrieb

- [Installation](INSTALLATION.md)
- [Betrieb](OPERATIONS.md)
- [Disaster Recovery](DISASTER_RECOVERY.md)
- [Backup-Server-Enrollment](BACKUP_SERVER_ENROLLMENT.md)
- [Backup-Kurzleitfaden](BACKUP_SETUP_QUICKSTART.md)
- [Uptime-Kuma-2-Migration](UPTIME_KUMA_2_MIGRATION.md)
- [Bot- und Crawler-Lastregeln](BOT_CRAWLER_POLICY.md)

## Fachliche Daten und Audits

- [Stammdaten-Go-Live-Review](MASTER_DATA_GO_LIVE_REVIEW.md)
- [Schiffskatalog-Audit](SHIP_SEED_SCREENSHOT_AUDIT.md)
- [Schiffsgeschwindigkeits-Audit](SHIP_SPEED_CONVERSION_AUDIT.md)
- [Munitionskatalog-Audit](AMMUNITION_SEED_AUDIT.md)
- [Upgrade-Katalog-Audit](UPGRADE_SEED_SCREENSHOT_AUDIT.md)
- [Build-Berechnungs-Audit](BUILD_CALCULATION_AUDIT.md)
- [Build-Option-Icons](BUILD_OPTION_ICONS.md)
- [Kampf-DPM-Analyse](COMBAT_DPM_ANALYSIS.md)
- [Ingame-Referenzbilder und Prüfsummen](ingame-screenshots/)

## Integrationen und Benachrichtigungen

- [Outbound-Webhooks](outbound-webhooks.md)
- [Webhook-Nachrichten-Templates](webhook-templates/)
- [Raid-Helper-Kalenderintegration](RAID_HELPER_CALENDAR.md)

## Pflege

- Jedes Thema hat genau ein führendes Dokument; andere Texte verlinken darauf, statt Anweisungen zu
  duplizieren.
- Verhaltens-, Konfigurations- und Migrationsänderungen aktualisieren die Dokumentation im selben
  Commit.
- Audit-Dokumente nennen Stand, geprüften Umfang und verbleibende Grenzen. Sie werden nicht als
  zeitlose Rechts- oder Betriebsfreigabe verstanden.
- Relative Links müssen innerhalb des Repositorys auflösbar sein; Beispiele enthalten keine echten
  Zugangsdaten oder personenbezogenen Daten.
