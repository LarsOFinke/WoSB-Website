# Dokumentation

Dieser Index ist der Einstieg für Entwicklung, Deployment und Betrieb. Die Dokumente sind nach
Verantwortung gruppiert; die alten Dateinamen wurden bewusst nicht als zweite
Quelle dupliziert.

## Agenten-Einstieg

- [Agent Onboarding](../.agents/ONBOARDING.md) – tokenarmer Schnellstart und
  Aufgabennavigation
- [Projekt-Cache](../.agents/PROJECT_CACHE.md) – stabile Systemlandkarte und
  bekannte Debugging-Grundlage
- [`AGENTS.md`](../AGENTS.md) – verbindliche Arbeitsregeln

Die `.agents`-Dokumente sind Navigationshilfen. Verbindliche Qualitäts-,
Architektur-, Security-, Datenschutz- und Betriebsregeln bleiben in den unten
aufgeführten Primärdokumenten.

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
- [Versionierung](development/VERSIONING.md)

## Deployment und Betrieb

- [CI/CD und Deployment](deployment/DEPLOYMENT.md)
- [Betrieb](deployment/OPERATIONS.md)
- [Backup-Server-Enrollment (Details)](deployment/BACKUP_SERVER_ENROLLMENT.md)

Uptime Kuma gehört nicht mehr zum Produktionsstack. Historische Ursache und
Entfernung sind im [Deployment-Incident-Index](debugging/DEPLOYMENT_INCIDENTS.md)
dokumentiert.

## Referenz und Integrationen

- [Referenzdokumente](reference/)
- [API-Nutzung und Sicherheit](reference/API.md)
- [Generierte API-Endpunktreferenz](reference/API_ENDPOINTS.md)
- [Outbound-Webhooks](integrations/outbound-webhooks.md)
- [Webhook-Templates](integrations/webhook-templates/README.md)
- [Ingame-Screenshot-Katalog](ingame-screenshots/README.md)

## Pflegevertrag

Verhaltensänderungen aktualisieren Implementierung, Tests und zugehörige Doku im
selben Arbeitsschritt. Änderungen an Topologie, Modulgrenzen, Gates oder zentralen
Debugging-Einstiegen aktualisieren zusätzlich Agent-Onboarding und Projekt-Cache.
Flüchtige Werte wie Branch, Revision und Dateizahlen werden nicht abgeschrieben,
sondern mit `bash .agents/scripts/project-context.sh` live ermittelt.
