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

# 3. Betroffenes Modul und bei Fehlern den Debugging-Cache öffnen
sed -n '1,260p' .agents/MODULE_CACHE.md
sed -n '1,220p' .agents/DEBUGGING_CACHE.md

# 4. Nach der Änderung passende Gates ermitteln
bash .agents/scripts/check-changes.sh
```

Danach nur die vom Auftrag betroffenen Primärdateien, deren direkte Aufrufer,
Tests, Konfiguration und Dokumentation lesen. Keine pauschale Volltextanalyse des
gesamten Repositorys beginnen, wenn der Cache bereits den Einstieg nennt.

Für einen ausdrücklich breiten Qualitäts- und Strukturputz gilt der tokenarme
Ablauf in [REPOSITORY_SPRING_CLEANING.md](REPOSITORY_SPRING_CLEANING.md).

## Feste Systemgrenzen

- Laufzeit: `Browser -> NGINX -> Spring Boot -> PostgreSQL`.
- `spring-api/` ist das einzige Backend; kein Python-Webbackend rekonstruieren.
- Frontend: Seite orchestriert, Composable hält Ablauf/Zustand, API-Modul macht
  Netzwerkzugriffe, Domain-Modul enthält reine Regeln.
- Backend: OpenAPI-Spezifikation -> generiertes API-DTO -> Modul-Controller ->
  Service -> Repository -> PostgreSQL. Controller besitzen Spring-MVC-Bindings und
  validieren DTOs direkt; Mapper übersetzen ausschließlich zwischen API-/Modul-DTOs,
  Entities und Repository-Zeilen.
  Fachlogik, Autorisierung und Transaktionen gehören in den Service; Controller
  und öffentliche Service-Grenzen kennen weder Entities noch JDBC-Zeilen/Roh-Maps.
- Schemaänderungen ausschließlich durch neue Flyway-Migrationen; veröffentlichte
  Migrationen nie bearbeiten. Hibernate bleibt auf `validate`.
- Deployment und Update starten am Ursprung über `deploy.sh`/`update.sh` und
  verwenden Artefakte, Backups, Flyway und Rollback. **Test ist immer das
  Standardziel**; Production darf nur mit `--production` angesprochen werden.
  Die Profile liegen getrennt in `.env.origin.test` und `.env.origin.production`.
  Produktionsdaten oder Docker-Volumes niemals als Diagnosemaßnahme löschen.
- Diagnostics starten am Ursprung über `infrastructure/scripts/diagnostics/debug.sh`
  und folgen derselben Zielauswahl: Test ohne Flag, Production mit
  `--production`. Remote wird begrenzt, lokal redigiert; keine Rohlogs oder
  Diagnosearchive auf dem Ziel erzeugen.
- Lokale `.env`, private Schlüssel, Tokens, personenbezogene Daten und
  vollständige IP-Adressen weder lesen/ausgeben noch versionieren, wenn sie für
  den konkreten Auftrag nicht zwingend erforderlich sind.

## Direkte Einstiege nach Aufgabentyp

| Aufgabe | Primärer Einstieg |
| --- | --- |
| Produktionsfehler | `infrastructure/scripts/diagnostics/debug.sh`, danach `docs/debugging/DEPLOYMENT_INCIDENTS.md` |
| Lokaler Modulfehler | `.agents/DEBUGGING_CACHE.md`, `docs/debugging/MODULE_DEBUGGING.md` |
| Modulverantwortung | `.agents/MODULE_CACHE.md`, danach `docs/architecture/MODULE_CATALOG.md` |
| Deployment/SSH | `docs/deployment/DEPLOYMENT.md`, `infrastructure/scripts/release/deploy-from-origin.sh` |
| Update/Backup/DB-Erhalt | `docs/debugging/2026-08-04-update-path-review.md` |
| Recovery | `docs/deployment/DISASTER_RECOVERY.md`, `tests/recovery/` |
| Backend-Domäne | `spring-api/src/main/java/eu/royalblackwater/api/<domain>/` |
| API-Spezifikation | `openapi/openapi.json`, danach `api/dto/*` und owning Modul-Controller |
| API-Nutzung/Endpunkte | `docs/reference/API.md`, `docs/reference/API_ENDPOINTS.md` |
| Tests und Gates | `docs/development/TESTING.md`, `Makefile`, `infrastructure/scripts/quality/validate.sh` |
| Versionierung/Releaseklasse | `docs/development/VERSIONING.md`, `.agents/scripts/next-version.sh` |
| Frontend-Funktion | `frontend/src/modules/<feature>/` |
| CSS/UI | `docs/reference/CSS_ARCHITECTURE.md`, betroffene Modulstile |
| Sicherheit | `SecurityConfiguration`, `security/`, `infrastructure/scripts/quality/security_audit.py` |
| Datenschutz | `privacy/`, `docs/reference/DATA_RETENTION.md` |

Skript-Ownership: Im Root liegen ausschließlich die öffentlichen Orchestratoren
`deploy.sh` und `update.sh`. Sämtliche gemeinsame Skriptlogik liegt modular unter
`infrastructure/scripts/`: `quality/` für Gates und Audits, `generation/` für
Generatoren, `release/` für Packaging/Deployment sowie fachliche Runtime-Module.
Das Release-Artefakt verwendet eine explizite Runtime-Allowlist; `quality/` und
`generation/` werden nicht auf das Ziel ausgeliefert. Modulgebundene Helfer unter
`.agents/scripts/` und `frontend/scripts/` verbleiben bei ihren Eigentümern.

Für Dateisuche zuerst `rg` beziehungsweise `rg --files` verwenden. Generierte API-DTOs und Locale-Ausgaben nicht von Hand bearbeiten; Controller-Routen sind Modulcode und werden gegen OpenAPI auditiert.

## Bekannter stabiler Stand

- Version: aus `VERSION` lesen; keine Zahl aus diesem Dokument übernehmen.
- Nächste Version tokenarm mit `bash .agents/scripts/next-version.sh
  patch|minor|major` bestimmen: Patch für Fixes, Minor für kompatible Features,
  Major für inkompatible oder ausdrücklich große Erweiterungen.
- Der interaktive First Run ist `./deploy.sh --configure`. Er kann den
  dedizierten `rbfadmin` samt Key über einen einmaligen VPS-Bootstrap-Zugang
  einrichten und danach im selben Lauf deployen.
- Folgedeployments verwenden den fest konfigurierten Key und `sudo -n`; der
  private Bootstrap-Account wird nicht persistiert.
- Zentrale API-Fehler erscheinen als `api_error`; Authentifizierungs- und
  Autorisierungsablehnungen als `security_401` beziehungsweise `security_403`.
  Keine Payloads oder Secrets zum Logging hinzufügen.
- `ApplicationIntegrationTest` prüft die laufende Spring-Anwendung über echtes
  HTTP gegen PostgreSQL/Testcontainers. Browser-Verträge liegen unter
  `frontend/tests/browser/` und mocken ausschließlich `/api/`-Anfragen.
- Ausführbare Java- und Frontend-JavaScript-Dateien sind auf 420 Zeilen begrenzt.
  Nur die dokumentierten deklarativen Locale-Kataloge sind ausgenommen.
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
bash .agents/scripts/check-all.sh
```

Der Scope-Helfer delegiert an bestehende Repository-Gates. Frontend-Tests nutzen
`bash .agents/scripts/check-frontend.sh`, das eine fehlende lokale `.env` nur
temporär aus `.env.example` erzeugt und garantiert wieder entfernt. Das Gate
enthält Chromium-Browser-Smokes; den Browser lokal einmalig mit
`cd frontend && npx playwright install chromium` bereitstellen.

Die Agenten-Gates sind absichtlich tokenarm: Bei Erfolg geben sie nur eine
Statuszeile aus, bei Fehlern einen begrenzten Log-Ausschnitt. Vollständige
Werkzeugausgabe lässt sich bei Bedarf mit `AGENT_GATE_VERBOSE=1` einschalten.
Direkte Einstiege sind:

```bash
bash .agents/scripts/check-backend.sh
bash .agents/scripts/check-frontend.sh
bash .agents/scripts/check-infrastructure.sh
bash .agents/scripts/check-docs.sh
bash .agents/scripts/check-cache.sh
bash .agents/scripts/check-all.sh
```

Lang laufende Befehle in ihrer bestehenden Prozess-Session weiterlaufen lassen.
Nicht durch enges Polling oder wiederholte Vollausgaben Tokens verbrauchen;
stattdessen auf Abschluss oder eine handlungsrelevante Fehlermeldung warten und
erst mit diesem Ergebnis weiterarbeiten. Einen noch laufenden Prozess nicht nur
wegen ausbleibender neuer Ausgabe neu starten.

Lokale, fachlich abgeschlossene Änderungen dürfen auf ausdrücklichen Wunsch als
kleine nachvollziehbare Einheiten committed werden. Commit und Push bleiben zwei
getrennte Entscheidungen: Pushes bewusst bündeln und nur ausdrücklich ausführen,
weil ein Push nach `main` externe CI einschließlich des aufwendigen NVD-
Dependency-Checks startet. Ein lokaler Commit benötigt keinen sofortigen Push.

## Cache aktualisieren

`PROJECT_CACHE.md` und diese Datei im selben Auftrag aktualisieren, wenn sich
Runtime-Topologie, Deployment-/Recovery-Ablauf, verbindliche Gates oder zentrale
Einstiege ändern. Neue/umbenannte Module aktualisieren zusätzlich
`MODULE_CACHE.md` und `docs/architecture/MODULE_CATALOG.md`; reproduzierte,
dauerhaft hilfreiche Fehlerursachen aktualisieren `DEBUGGING_CACHE.md` und das
passende Runbook. `check-cache.sh` prüft die Bestandsvollständigkeit. Flüchtige
Fakten wie Branch, Revision, Datei- oder Testanzahl bleiben aus dem Textcache
heraus und werden über `project-context.sh` live ermittelt.
