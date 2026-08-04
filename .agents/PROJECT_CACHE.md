# Projekt-Cache für Repository-Agenten

> Erfasst am 2026-08-04. Dieser Cache ist ein Navigationsindex, keine verbindliche
> Quelle. Vor Änderungen immer `AGENTS.md`, betroffene Dateien, Aufrufer, Tests,
> Konfiguration und Dokumentation lesen. Bei Widersprüchen gilt der Quellcode bzw.
> die unten genannte Primärquelle.
>
> Neuer Agent? Zuerst [ONBOARDING.md](ONBOARDING.md) lesen; dort steht der
> kürzeste sichere Einstieg einschließlich Live-Snapshot und Prüfauswahl.

## Schnellbild

- Produkt: **Royal Blackwater Fleet**, ein Fleet-Operations-Portal für World of
  Sea Battle. Die aktuelle Version immer aus `VERSION` lesen.
- Laufzeit: `Browser -> NGINX -> Spring Boot API -> PostgreSQL`.
- Backend: Java 21, Spring Boot 4.1, Maven 3.9, Spring Security, JPA/JDBC,
  MapStruct, Flyway, PostgreSQL und Testcontainers.
- Frontend: Vue 3.5, Vue Router 4, Vite 8, Node 22 und Playwright Chromium;
  JavaScript ohne TypeScript.
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
  ausführbarer Verantwortung bleiben grundsätzlich unter 420 Zeilen. Dieselbe
  harte Grenze gilt für ausführbare Frontend-JavaScript-Module; ausgenommen sind
  nur die geprüften deklarativen Locale-Module und `autoLocalizationCatalog.js`.
- Mockito wird im Maven-Testprozess als expliziter Startup-Agent geladen; die
  Dependency-Property löst den Pfad auch bei abweichendem lokalen Maven-Repository
  auf. Dynamisches Self-Attach ist kein Bestandteil des Testablaufs.
- Schemaänderungen ausschließlich als neue unveränderliche Flyway-Migration.
  Bestehende Systeme behalten die unveränderte V1-Historie; neue Datenbanken
  verwenden den B2-Marker und die fachlich getrennten V3–V7-Migrationen. Neue
  Schemaarbeit beginnt als kleine Vorwärtsmigration ab V8.
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
- Build-Druck trennt Modellbildung (`buildPrintModel.js`), Bild-Einbettung
  (`buildPrintImageEmbedding.js`) und SVG-/Dokument-Orchestrierung
  (`buildPrintExport.js`). Lokalisierungsverhalten liegt in
  `autoLocalization.js`, der große Übersetzungskatalog separat in
  `autoLocalizationCatalog.js`.
- Browser-Smokes liegen unter `frontend/tests/browser/`. Sie starten Vite und
  mocken nur `/api/`; echte Security-, Session-, CSRF- und Origin-Grenzen prüft
  `spring-api/src/test/java/eu/royalblackwater/api/integration/ApplicationIntegrationTest.java`
  gegen PostgreSQL.

## Infrastruktur und Betriebsgrenzen

- Öffentliche Ursprungseinstiege: `deploy.sh` und `update.sh`; beide delegieren an
  `infrastructure/scripts/release/deploy-from-origin.sh`.
- `./deploy.sh --configure` ist der vollständige interaktive First Run: Ziel,
  dedizierter `rbfadmin`, optional erzeugter Ed25519-Key, einmaliger VPS-
  Bootstrap-Zugang und Deployment laufen in einem Ablauf. Bootstrap-Zugangsdaten
  werden nicht in `.env.origin` persistiert. Normale Folgeläufe verwenden nur den
  geprüften Key-Zugang und `sudo -n`.
- Das interne Setup ist unter
  `infrastructure/scripts/setup/{options,workflow,main}.sh` getrennt.
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

## Stabiler Debugging-Ausgangspunkt (2026-08-04)

- Deployment-/Update-Primärdoku: `docs/deployment/DEPLOYMENT.md` und
  `docs/debugging/2026-08-04-update-path-review.md`.
- Bekannte Produktionsfehler und geprüfte Ursachen:
  `docs/debugging/DEPLOYMENT_INCIDENTS.md`. Dort zuerst nach Symptom suchen,
  bevor Logs oder Abläufe erneut vollständig kartiert werden.
- API-Fehler werden zentral als `api_error` mit Status, Methode, Pfad und
  ausnahmebezogener Ursache protokolliert; keine Request-Payloads oder Secrets in
  Logs ergänzen. Sicherheitsablehnungen bleiben separat als `security_401` bzw.
  `security_403` sichtbar.
- Der Release-Ablauf hält PostgreSQL-Daten unter dem gemeinsamen Installationsroot,
  erstellt vor Updates koordinierte Backups, lässt Flyway migrieren und stellt bei
  fehlgeschlagener Aktivierung Release und Backup wieder her. Niemals Volumes oder
  Datenverzeichnisse als vermeintliche Fehlerbehebung löschen.
- Das Cookie-Consent-UI öffnet ohne gespeicherte Entscheidung nicht automatisch,
  solange keine optionale Cookie-/Tracking-Integration aktiv ist. Manuelles Öffnen
  bleibt über Footer und Datenschutzcenter möglich.
- API-Nutzung und Sicherheitsgrenzen stehen in `docs/reference/API.md`; der
  vollständige Endpunktindex wird aus `contracts/api-contract.json` nach
  `docs/reference/API_ENDPOINTS.md` generiert.
- Historische Audit-Snapshots werden nicht mehr als zweite Dokumentationsquelle
  gepflegt. Aktuelle Soll-Regeln stehen ausschließlich in Architektur-,
  Entwicklungs-, Referenz- und Betriebsdokumenten.

## Häufige Befehle

```bash
make test          # schneller, ggf. Toolchains überspringender Prüfpfad
make validate      # vollständiges Release-Gate; identisch zu make test-full
make spring-test   # Maven verify
make frontend-test # Frontend-Test, Produktionsbuild und Chromium-Smokes
make check-tree    # strikte Repository-Hygiene
make build         # Spring-Paket plus Frontend-Build
make package-release
```

Agenten-Helfer für wiederkehrende Bestandsaufnahme und Prüfauswahl:

```bash
bash .agents/scripts/project-context.sh       # kompakter, stets aktueller Projekt-/Git-Snapshot
bash .agents/scripts/check-changes.sh         # Prüfempfehlung aus den geänderten Pfaden
bash .agents/scripts/check-changes.sh --run   # empfohlene vorhandene Repository-Gates ausführen
bash .agents/scripts/check-backend.sh         # Maven-/PostgreSQL-Gate, kompakte Ausgabe
bash .agents/scripts/check-frontend.sh        # Frontend-Test/Build/Browser-Smoke mit temporärer .env
bash .agents/scripts/check-infrastructure.sh  # Infrastruktur-/Update-Verträge, kompakte Ausgabe
bash .agents/scripts/check-docs.sh            # lokale Markdown-Links, Befehle und Doku-Generierung
bash .agents/scripts/check-all.sh             # make validate mit kompakter Ausgabe
```

Die Helfer enthalten keine eigene Fachprüfung. Sie lesen den aktuellen Stand und
delegieren an `make`, `scripts/test-*.sh` und `check_repository.py`, damit keine
zweite, später abweichende Qualitätslogik entsteht. Dokumentationsinvarianten
liegen entsprechend in `scripts/check_documentation.py`; `check-docs.sh` ist nur
der tokenarme Einstieg. Erfolgreiche Gates liefern eine Statuszeile, Fehler die
letzten 200 Logzeilen. `AGENT_GATE_VERBOSE=1` schaltet die vollständige Ausgabe
für gezielte Diagnose ein.

`scripts/test.sh full` führt statische Repository-, Security-, Spring- und
CSS-Audits, Java-Syntaxprüfung, Infrastruktur-/Update-Tests, Recovery-Pytests,
`mvn verify`, Frontend-Tests/Build/Chromium-Smokes und abschließend `--strict-tree`
aus. Playwright-Chromium wird lokal einmalig mit `npx playwright install chromium`
im `frontend/` installiert. Für kleine
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
3. Fokussierte Unit-/Domain-Tests plus Page-Binding-, Locale-, Responsive-,
   Browser- und Build-Prüfung nach Relevanz.

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
Für den flüchtigen Stand zuerst `bash .agents/scripts/project-context.sh` ausführen;
dadurch müssen Branch, Version, Arbeitsbaum und Debugging-Einstiege nicht aus
älteren Sitzungszusammenfassungen rekonstruiert werden.
