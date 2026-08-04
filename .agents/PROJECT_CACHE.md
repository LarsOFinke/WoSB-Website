# Projekt-Cache für Repository-Agenten

> Erfasst am 2026-08-04. Dieser Cache ist ein Navigationsindex, keine verbindliche
> Quelle. Vor Änderungen immer `AGENTS.md`, betroffene Dateien, Aufrufer, Tests,
> Konfiguration und Dokumentation lesen. Bei Widersprüchen gilt der Quellcode bzw.
> die unten genannte Primärquelle.

## Schnellbild

- Produkt: **Royal Blackwater Fleet**, ein Fleet-Operations-Portal für World of
  Sea Battle, Version `1.0.0`.
- Laufzeit: `Browser -> NGINX -> Spring Boot API -> PostgreSQL`.
- Backend: Java 21, Spring Boot 4.1, Maven 3.9, Spring Security, JPA/JDBC,
  MapStruct, Flyway, PostgreSQL und Testcontainers.
- Frontend: Vue 3.5, Vue Router 4, Vite 8, Node 22; JavaScript ohne TypeScript.
- Betrieb: Docker Compose, NGINX, systemd-Runner sowie artefaktbasierte Release-,
  Update-, Backup- und Restore-Abläufe.
- Das frühere Python-Backend ist nicht mehr Teil der Laufzeit. Python wird für
  Repository-, Infrastruktur-, Packaging- und Recovery-Werkzeuge verwendet.

## Verbindliche Einstiegspunkte

| Thema | Zuerst lesen |
| --- | --- |
| Arbeitsregeln | `AGENTS.md`, `docs/development/QUALITY_STANDARDS.md` |
| Gesamtsystem | `README.md`, `docs/architecture/ARCHITECTURE.md` |
| Backend | `spring-api/README.md`, `spring-api/pom.xml`, `spring-api/src/main/resources/application.yml` |
| Frontend | `frontend/ARCHITECTURE.md`, `frontend/package.json`, `docs/reference/CSS_ARCHITECTURE.md` |
| Datenbank | `docs/development/DATABASE.md`, `spring-api/src/main/resources/db/migration/` |
| Tests | `docs/development/TESTING.md`, `Makefile`, `scripts/test.sh` |
| Infrastruktur | `infrastructure/ARCHITECTURE.md`, `infrastructure/README.md`, `infrastructure/compose.yml` |
| Betrieb/Recovery | `docs/deployment/OPERATIONS.md`, `docs/deployment/DISASTER_RECOVERY.md` |
| HTTP-Vertrag | `contracts/api-contract.json` |
| Webhooks/Build-Daten | `contracts/webhook-events.json`, `contracts/build-*.json` |

Der Dokumentationsindex ist `docs/README.md`. Änderungen an Verhalten oder
Betriebsabläufen schließen die zugehörige Dokumentation ein.

## Repository-Landkarte

```text
spring-api/      alleinige Backend-Laufzeit, Security, Fachdomänen, Persistenz
frontend/        Vue-Anwendung, Feature-Module, Lokalisierung und UI-Tests
contracts/       versionierte HTTP-, Build-, Backup- und Webhook-Verträge
infrastructure/  Compose, NGINX, Setup, Release, Update, Backup und Restore
scripts/         Qualitäts-, Security-, Packaging- und Repository-Werkzeuge
tests/recovery/  sprachneutrale Recovery-/Remote-Sync-Vertragstests
docs/            Architektur, Entwicklung, Betrieb, Referenz und Audits
.github/         CI-, Security-, Release- und Deployment-Workflows
```

Nicht von Hand bearbeiten oder versionieren: `frontend/src/locales/generated/`,
`frontend/dist/`, `node_modules/`, `spring-api/target/`, Python-Caches, lokale
`.env`-Dateien, Runtime-Daten und Release-Artefakte. Die vorhandenen Verzeichnisse
`release/` und `release-arm64/` sind generierte/ignorierte Ausgaben.

## Backend-Navigation

- Composition/Querschnitt: `config`, `core`, `contract`, `operations`,
  `persistence`, `transport`, `transport/generated`.
- Fachdomänen: `account`, `audit`, `builds`, `calendar`, `content`, `files`,
  `fleet`, `forum`, `groups`, `guides`, `legal`, `masterdata`, `onboarding`,
  `privacy`, `raidhelper`, `security`, `securityops`, `ships`, `squads`, `webhooks`.
- Generierte Controller validieren den HTTP-Transport und delegieren anhand der
  `operationId` an genau einen Handler; fehlende oder doppelte Handler verhindern
  den Start.
- Controller/Handler orchestrieren nur. Autorisierung, Fachlogik, Transaktionen
  und notwendiges Audit gehören in Services; Abhängigkeiten per Konstruktor.
- Spring Security ist die einzige Sicherheitsgrenze. Router-/UI-Guards sind nur
  UX. Private Mutationen benötigen Session, CSRF sowie Host-/Origin-Prüfung.
- Hibernate: `ddl-auto=validate`, `open-in-view=false`; Responses dürfen keine
  Lazy-Load-Abfragen auslösen. Wachsende Listen brauchen begrenzte Suche,
  Pagination und Domänenfilter; Collections gebündelt/projiziert laden.
- MapStruct kompiliert mit `unmappedTargetPolicy=ERROR`. Java-Dateien mit
  ausführbarer Verantwortung bleiben grundsätzlich unter 420 Zeilen.
- Schemaänderungen ausschließlich als neue unveränderliche Flyway-Migration.
  Aktueller Stand bei Erfassung: nur `V1__current_schema_baseline.sql`.
- Referenzdaten liegen unter `spring-api/src/main/resources/seed` und werden
  idempotent angewendet; administrative Overrides bewusst erhalten.

## Frontend-Navigation

- Einstieg: `frontend/src/main.js`; Routing: `frontend/src/router/index.js`.
- Feature-Module liegen unter `frontend/src/modules/<feature>/` und verwenden je
  nach Bedarf `api/`, `domain/`, `composables/`, `components/`, `pages/`.
- Abhängigkeitsrichtung: `page -> composable -> api/domain` und
  `page -> component`. Seiten rufen keine API direkt auf und besitzen keine
  asynchronen Workflows.
- Routenmodule existieren für Accounts, Admin, Builds, Calendar, Combat, Fleet,
  Forum, Groups, Guides, Onboarding, Privacy, Legal und Squads.
- Transport gehört in API-Module, deterministische Regeln in `domain`, Zustand,
  Lifecycle und Abläufe in Composables, wiederverwendbare UI in Komponenten.
- Gemeinsame Infrastruktur: `core/`, `shared/`, `config/`, `router/`, `locales/`
  und `styles/`.
- Frontend-Guards prüfen Gast/User/Staff/Admin/Fleet-Management, ersetzen aber nie
  serverseitige Autorisierung.
- Lokalisierungsquellen: `frontend/src/locales/messages/`; Generator:
  `frontend/scripts/generate-locales.mjs`. Englisch ist synchroner Fallback,
  andere Locales werden dynamisch geladen.
- Globale CSS-Kaskade: acht geordnete Imports aus
  `frontend/src/styles/global/index.js`; Reihenfolge ist Architekturvertrag.
  Feature-Stile bleiben beim Modul.

## Infrastruktur und Betriebsgrenzen

- Öffentliche Ursprungseinstiege: `deploy.sh` und `update.sh`; beide delegieren an
  `infrastructure/scripts/release/deploy-from-origin.sh`.
- Setup ist in `scripts/setup/{options,workflow,main}.sh` getrennt.
- Host-Helfer liegen unter `scripts/lib/host/` (Pakete, Storage, Firewall, TLS,
  Control); Skripte müssen robust, idempotent und mit klaren Fehlercodes arbeiten.
- Die API führt keine privilegierten Host-Befehle aus. Sie schreibt restriktive
  JSON-Anforderungen in eine Inbox; root-eigene systemd-Runner übernehmen sie.
- Produktion nutzt kompilierte, prüfsummenbewehrte, source-freie Artefakte.
  Ursprungstransfer: `./deploy.sh`; Update: `./update.sh`; Zielserver-Wrapper:
  `infrastructure/scripts/release/setup_website.sh`.
  Origin-Verbindung wird interaktiv in `.env.origin` gespeichert
  (`.env.origin.example` ist die Vorlage).
  Verifier und Rollback liegen unter `infrastructure/scripts/release/`.
- Backup/Restore koppeln Anwendung, Flyway-Schema, persistente Dateien und das
  zugehörige Release-Artefakt. Restore ist gestaged und fail-closed.
- Outbound-Netzwerk ist auf explizite Integrationen begrenzt. Webhooks enthalten
  knappe Audit-/Aktionshinweise und dürfen den Hauptablauf nicht unkontrolliert
  blockieren.

## Häufige Befehle

```bash
make test          # schneller, ggf. Toolchains überspringender Prüfpfad
make validate      # vollständiges Release-Gate; identisch zu make test-full
make spring-test   # Maven verify
make frontend-test # Frontend-Test plus Produktionsbuild
make check-tree    # strikte Repository-Hygiene
make build         # Spring-Paket plus Frontend-Build
make package-release
```

`scripts/test.sh full` führt statische Repository-, Security-, Spring- und
CSS-Audits, Java-Syntaxprüfung, Infrastruktur-/Update-Tests, Recovery-Pytests,
`mvn verify`, Frontend-Tests/Build und abschließend `--strict-tree` aus. Für kleine
Änderungen zuerst gezielt testen, danach die betroffenen Gates; bei
querschnittlichen Änderungen `make validate`.

## Änderungs-Checklisten

### API oder Backend-Domäne

1. Vertrag/Operation, generierten Transport, Handler, Service, Repository/Mapper,
   Security und Audit gemeinsam verfolgen.
2. Erfolgs-, Fehler- und Berechtigungsfälle ergänzen; bei Listen auch Filter,
   Grenzwerte und Query-Anzahl prüfen.
3. Keine PII, Tokens, vollständigen IP-Adressen oder Secrets in Logs, Fehlern,
   Fixtures oder Webhooks.

### Datenmodell

1. Entity/SQL-Nutzung und Recovery-/Upgrade-Pfad prüfen.
2. Neue Flyway-Datei hinzufügen; veröffentlichte Migrationen nie ändern.
3. Indizes für Filter/Sortierung, Hibernate-Validierung und Restore prüfen.

### Frontend-Funktion

1. Ablauf in Composable, Transport in API, reine Regeln in Domain, Seite nur als
   Komposition; vorhandene Komponenten/Tokens wiederverwenden.
2. Barrierefreiheit, responsive CSS, Übersetzungen und serverseitige
   Berechtigung beachten.
3. Fokussierte Unit-/Domain-Tests plus Page-Binding-, Locale-, Responsive- und
   Build-Prüfung nach Relevanz.

### Infrastruktur/Release/Recovery

1. Wrapper, Aufrufer, systemd-/Compose-Verträge und Betriebsdokumentation lesen.
2. Atomare Dateiänderungen, Idempotenz, Rechte, Secret-Leaks, Fehlercodes und
   Rollback/Recovery bedenken.
3. Infrastruktur-, Update-, Artefakt-, Tamper- und Recovery-Tests passend wählen.

## Cache-Pflege

Cache neu prüfen, wenn `AGENTS.md`, `README.md`, Architektur-/Qualitätsdokumente,
`pom.xml`, `package.json`, `Makefile`, `scripts/test.sh`, Modulverzeichnisse oder
Runtime-/Deployment-Topologie geändert wurden. Keine flüchtigen Dateizahlen,
Testzahlen oder Vertragsoperationszahlen als Entscheidungsgrundlage verwenden;
bei Bedarf direkt mit `rg`, `find` oder dem jeweiligen Parser ermitteln.
