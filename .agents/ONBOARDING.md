# Agent Onboarding – Royal Blackwater Fleet

Diese Datei ist der tokenarme Einstieg für neue Repository-Agenten. Sie ersetzt
nicht `AGENTS.md` oder technische Primärquellen. Ziel ist, bekannte Architektur
und Debugging-Grundlagen nicht bei jedem Auftrag erneut vollständig zu suchen.

## Start in unter einer Minute

```bash
# 1. Aktuellen, geheimnisfreien Zustand ausgeben
bash .agents/scripts/project-context.sh

# 2. Gepflegte Systemlandkarte lesen
sed -n '1,260p' .agents/PROJECT_CACHE.md

# 3. Nach der Änderung passende Gates ermitteln
bash .agents/scripts/check-changes.sh
```

Danach nur die vom Auftrag betroffenen Primärdateien, deren direkte Aufrufer,
Tests, Konfiguration und Dokumentation lesen. Keine pauschale Volltextanalyse des
gesamten Repositorys beginnen, wenn der Cache bereits den Einstieg nennt.

## Feste Systemgrenzen

- Laufzeit: `Browser -> NGINX -> Spring Boot -> PostgreSQL`.
- `spring-api/` ist das einzige Backend; kein Python-Webbackend rekonstruieren.
- Frontend: Seite orchestriert, Composable hält Ablauf/Zustand, API-Modul macht
  Netzwerkzugriffe, Domain-Modul enthält reine Regeln.
- Backend: generierter Controller -> Operation-Handler -> Service ->
  Repository/Mapper. Fachlogik, Autorisierung und Transaktionen gehören in den
  Service.
- Schemaänderungen ausschließlich durch neue Flyway-Migrationen; veröffentlichte
  Migrationen nie bearbeiten. Hibernate bleibt auf `validate`.
- Deployment und Update starten am Ursprung über `deploy.sh`/`update.sh` und
  verwenden Artefakte, Backups, Flyway und Rollback. Produktionsdaten oder
  Docker-Volumes niemals als Diagnosemaßnahme löschen.
- Lokale `.env`, private Schlüssel, Tokens, personenbezogene Daten und
  vollständige IP-Adressen weder lesen/ausgeben noch versionieren, wenn sie für
  den konkreten Auftrag nicht zwingend erforderlich sind.

## Direkte Einstiege nach Aufgabentyp

| Aufgabe | Primärer Einstieg |
| --- | --- |
| Produktionsfehler | `docs/debugging/DEPLOYMENT_INCIDENTS.md` |
| Deployment/SSH | `docs/deployment/DEPLOYMENT.md`, `infrastructure/scripts/release/deploy-from-origin.sh` |
| Update/Backup/DB-Erhalt | `docs/debugging/2026-08-04-update-path-review.md` |
| Recovery | `docs/deployment/DISASTER_RECOVERY.md`, `tests/recovery/` |
| Backend-Domäne | `spring-api/src/main/java/eu/royalblackwater/api/<domain>/` |
| API-Vertrag | `contracts/api-contract.json`, danach generierter Transport und Handler |
| API-Nutzung/Endpunkte | `docs/reference/API.md`, `docs/reference/API_ENDPOINTS.md` |
| Frontend-Funktion | `frontend/src/modules/<feature>/` |
| CSS/UI | `docs/reference/CSS_ARCHITECTURE.md`, betroffene Modulstile |
| Sicherheit | `SecurityConfiguration`, `security/`, `scripts/security_audit.py` |
| Datenschutz | `privacy/`, `docs/reference/DATA_RETENTION.md` |

Für Dateisuche zuerst `rg` beziehungsweise `rg --files` verwenden. Generierte
Controller und Locale-Ausgaben nicht von Hand bearbeiten.

## Bekannter stabiler Stand

- Version: aus `VERSION` lesen; keine Zahl aus diesem Dokument übernehmen.
- Der interaktive First Run ist `./deploy.sh --configure`. Er kann den
  dedizierten `rbfadmin` samt Key über einen einmaligen VPS-Bootstrap-Zugang
  einrichten und danach im selben Lauf deployen.
- Folgedeployments verwenden den fest konfigurierten Key und `sudo -n`; der
  private Bootstrap-Account wird nicht persistiert.
- Zentrale API-Fehler erscheinen als `api_error`; Authentifizierungs- und
  Autorisierungsablehnungen als `security_401` beziehungsweise `security_403`.
  Keine Payloads oder Secrets zum Logging hinzufügen.
- Cookie-Einstellungen öffnen ohne vorhandene Entscheidung nicht automatisch,
  solange keine optionale Cookie-/Tracking-Integration aktiv ist. Der manuelle
  Einstieg bleibt über Footer und Datenschutzcenter erhalten.
- Bestehende Datenbanken behalten die unveränderte Flyway-V1-Historie; neue
  Datenbanken starten über B2 und die modularen V3–V7-Dateien. Neue Änderungen
  werden ab V8 als kleine fachliche Vorwärtsmigration ergänzt.

## Prüfung ohne erneute Gate-Recherche

```bash
# Empfehlung nur anzeigen
bash .agents/scripts/check-changes.sh

# Empfehlung ausführen
bash .agents/scripts/check-changes.sh --run

# Vollständiges Gate bei querschnittlichen Änderungen
make validate
```

Der Scope-Helfer delegiert an bestehende Repository-Gates. Frontend-Tests nutzen
`bash .agents/scripts/check-frontend.sh`, das eine fehlende lokale `.env` nur
temporär aus `.env.example` erzeugt und garantiert wieder entfernt.

## Cache aktualisieren

`PROJECT_CACHE.md` und diese Datei im selben Auftrag aktualisieren, wenn sich
Runtime-Topologie, Hauptmodule, Deployment-/Recovery-Ablauf, verbindliche Gates
oder zentrale Debugging-Einstiege ändern. Flüchtige Fakten wie Branch, Revision,
Datei- oder Testanzahl bleiben aus dem Textcache heraus und werden über
`project-context.sh` live ermittelt.
