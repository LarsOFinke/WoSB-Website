# Dokumentation

Dieser Index ist der Einstieg für das v1.0-Deployment. Die Dokumente sind nach
Verantwortung gruppiert; die alten Dateinamen wurden bewusst nicht als zweite
Quelle dupliziert.

## Frischeinrichtung (zwei Server)

1. [Webseiten-Server installieren](deployment/INSTALLATION.md)
2. [Backup-Server per Enrollment einrichten](deployment/BACKUP_SETUP_QUICKSTART.md)
3. [Go-Live-Prüfung](deployment/GO_LIVE.md)
4. [Betrieb und Updates](deployment/OPERATIONS.md)
5. [Disaster Recovery](deployment/DISASTER_RECOVERY.md)

Der Ablauf ist für einen frischen Webseiten-Server und einen getrennten
Backup-/Recovery-Server ausgelegt. Die Installationsanleitung enthält
Voraussetzungen, sichere Defaults, Smoke-Tests und die erwarteten Ergebnisse.

## Architektur und Sicherheit

- [Architektur](architecture/ARCHITECTURE.md)
- [Backup-Architektur](architecture/BACKUP_ARCHITECTURE.md)
- [Container-Sicherheit und Isolation](architecture/CONTAINER_SECURITY.md)

## Entwicklung und Qualitätsgates

- [Entwicklung](development/DEVELOPMENT.md)
- [Tests](development/TESTING.md)
- [Datenbank und Migrationen](development/DATABASE.md)
- [Qualitätsstandards](development/QUALITY_STANDARDS.md)

## Deployment und Betrieb

- [CI/CD und Deployment](deployment/DEPLOYMENT.md)
- [Betrieb](deployment/OPERATIONS.md)
- [Uptime-Kuma-Migration](deployment/UPTIME_KUMA_2_MIGRATION.md)
- [Backup-Server-Enrollment (Details)](deployment/BACKUP_SERVER_ENROLLMENT.md)

## Audits und Reviews

Alle Audits, Seed-Reviews und Qualitätsberichte liegen unter [audits/](audits/).

## Referenz und Integrationen

- [Referenzdokumente](reference/)
- [Outbound-Webhooks](integrations/outbound-webhooks.md)
- [Webhook-Templates](integrations/webhook-templates/README.md)
- [Ingame-Screenshot-Katalog](ingame-screenshots/README.md)
