# Projekt-Cache für Repository-Agenten

> Geprüft am 2026-08-05. Dieser Cache ist ein Navigationsindex, keine verbindliche
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
| Arbeitsregeln | `AGENTS.md`, `docs/development/QUALITY_STANDARDS.md`, `docs/development/VERSIONING.md` |
| Gesamtsystem | `README.md`, `docs/architecture/ARCHITECTURE.md` |
| Modulverantwortung | `docs/architecture/MODULE_CATALOG.md`, `.agents/MODULE_CACHE.md` |
| Debugging | `.agents/DEBUGGING_CACHE.md`, `docs/debugging/MODULE_DEBUGGING.md` |
| Backend | `spring-api/README.md`, `spring-api/pom.xml`, `spring-api/src/main/resources/application.yml` |
| Frontend | `frontend/ARCHITECTURE.md`, `frontend/package.json`, `docs/reference/CSS_ARCHITECTURE.md` |
| Datenbank | `docs/development/DATABASE.md`, `spring-api/src/main/resources/db/migration/` |
| Legacy-Datenmigration | `docs/debugging/LEGACY_BUILD_DATA_MIGRATION.md` |
| Tests | `docs/development/TESTING.md`, `Makefile`, `infrastructure/scripts/quality/validate.sh` |
| Breiter Qualitätsputz | `.agents/REPOSITORY_SPRING_CLEANING.md` |
| Infrastruktur | `infrastructure/ARCHITECTURE.md`, `infrastructure/README.md`, `infrastructure/compose.yml` |
| Betrieb/Recovery | `docs/deployment/OPERATIONS.md`, `docs/deployment/DISASTER_RECOVERY.md` |
| HTTP-Vertrag | `openapi/openapi.json` |
| Webhooks/Build-Daten | `spring-api/src/main/reference/webhook-events.json`, `spring-api/src/main/reference/build-stat-catalog.json` |

Der Dokumentationsindex ist `docs/README.md`. Änderungen an Verhalten oder
Betriebsabläufen schließen die zugehörige Dokumentation ein.

## Repository-Landkarte

```text
spring-api/      alleinige Backend-Laufzeit, Security, Fachdomänen, Persistenz
frontend/        Vue-Anwendung, Feature-Module, Lokalisierung und UI-Tests
openapi/         versionierte externe HTTP-Spezifikation
infrastructure/  Compose und zentrale Skriptmodule für Quality, Generation und Runtime
tests/recovery/  sprachneutrale Recovery-/Remote-Sync-Vertragstests
docs/            Architektur, Entwicklung, Betrieb, Referenz und Audits
.github/         CI-, Security-, Release- und Deployment-Workflows
```

Nicht von Hand bearbeiten oder versionieren: `frontend/src/locales/generated/`,
`frontend/dist/`, `node_modules/`, `spring-api/target/`, Python-Caches, lokale
`.env`-Dateien, Runtime-Daten und Release-Artefakte. Die vorhandenen Verzeichnisse
`release/` und `release-arm64/` sind generierte/ignorierte Ausgaben.

## Backend-Navigation

Der vollständige pfadgenaue Modulbestand mit Verantwortung und Diagnoseeinstieg
steht im `docs/architecture/MODULE_CATALOG.md`; die tokenarme Auswahl steht in
`.agents/MODULE_CACHE.md`. Keine Modulverantwortung aus dem Verzeichnisnamen
allein ableiten.

- Composition/Querschnitt: `config`, `core`, `operations`, `persistence`, `shared`
  und die generierten `api/dto`-Transportmodelle.
- Fachdomänen: `account`, `audit`, `builds`, `calendar`, `content`, `files`,
  `fleet`, `forum`, `groups`, `guides`, `legal`, `masterdata`, `onboarding`,
  `privacy`, `raidhelper`, `security`, `securityops`, `ships`, `squads`, `webhooks`.
- `openapi/openapi.json` definiert den externen HTTP-Transport; generierte
  `api/dto/*`-Records bilden dessen Request-/Response-Typen. Modul-Controller besitzen
  die Spring-MVC-Bindings direkt; fehlende, doppelte oder abweichende Routen brechen
  `audit_controller_contract.py`.
- Controller orchestrieren nur und kennen weder Entities noch Repositories.
  Autorisierung, Fachlogik, Transaktionen und notwendiges Audit gehören in
  Services; Persistenzzugriff erfolgt über Modul-Repositories. Öffentliche
  Service-Grenzen transportieren API- oder Modul-DTOs, keine JDBC-Zeilen,
  Roh-Maps oder Entities. Zeilen-/Entity-Konvertierung gehört in Mapper.
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

- Öffentliche Root-Einstiege sind ausschließlich `deploy.sh` und `update.sh`;
  beide delegieren an `infrastructure/scripts/release/deploy-from-origin.sh`.
  Produktionsdiagnosen starten direkt über
  `infrastructure/scripts/diagnostics/debug.sh`.
- `./deploy.sh --configure` ist der vollständige interaktive First Run für den
  **Testserver**. Production wird ausschließlich mit
  `./deploy.sh --production --configure` eingerichtet. Bootstrap-Zugangsdaten
  werden nicht persistiert; normale Folgeläufe verwenden nur den geprüften
  Key-Zugang und `sudo -n`.
- Origin-Ziele sind strikt getrennt: `.env.origin.test` ist der Default für
  `deploy.sh`, `update.sh` und Diagnostics; `.env.origin.production` wird nur
  nach explizitem `--production` geladen. Keine automatische Legacy-Fallback-
  Auswahl auf `.env.origin` zulassen.
- Das interne Setup ist unter
  `infrastructure/scripts/setup/{options,workflow,main}.sh` getrennt.
- Host-Helfer liegen unter `infrastructure/scripts/lib/host/` (Pakete, Storage,
  Firewall, TLS, Control); Skripte müssen robust, idempotent und mit klaren
  Fehlercodes arbeiten. Alle gemeinsamen Repository-Skripte liegen modular unter
  `infrastructure/scripts/`: `quality/`, `quality/tests/`, `generation/`,
  `release/` und die fachlichen Runtime-Module. Ein top-level `scripts/` darf
  nicht neu eingeführt werden.
- Der Deployment-Packager kopiert Runtime-Module über eine explizite Allowlist.
  `quality/`, `generation/` und die Packaging-Skripte selbst dürfen nicht im
  Produktionsartefakt landen. `.agents/scripts/` und `frontend/scripts/` bleiben
  als eigentümergebundene Modulhelfer bestehen.
- Die API führt keine privilegierten Host-Befehle aus. Sie schreibt restriktive
  JSON-Anforderungen in eine Inbox; root-eigene systemd-Runner übernehmen sie.
- Produktion nutzt kompilierte, prüfsummenbewehrte, source-freie Artefakte.
  Ursprungstransfer: `./deploy.sh`; Update: `./update.sh`; beide verwenden ohne
  Flag den Testserver. Production erfordert `--production`. Zielserver-Wrapper:
  `infrastructure/scripts/release/setup_website.sh`. Origin-Verbindungen werden
  getrennt in `.env.origin.test` und `.env.origin.production` gespeichert; die
  gleichnamigen `.example`-Dateien sind die Vorlagen.
  Verifier und Rollback liegen unter `infrastructure/scripts/release/`.
- Backup/Restore koppeln Anwendung, Flyway-Schema, persistente Dateien und das
  zugehörige Release-Artefakt. Restore ist gestaged und fail-closed.
- Ein bewusst begrenzter Legacy-Teilrestore (z. B. Python→Java Builds) ist dagegen eine
  logische Datenmigration gegen das bereits aktuelle Flyway-Schema: keine alten numerischen
  FKs, User/Auth-/Masterdata oder DDL übernehmen. Referenzen semantisch auflösen, exakt dieselbe
  Importdatei erst auf Test und danach Production verwenden und auf beiden Zielen vor Commit einen
  vollständigen transaktionalen Dry-Run verlangen.
- Outbound-Netzwerk ist auf explizite Integrationen begrenzt. Webhooks enthalten
  knappe Audit-/Aktionshinweise und dürfen den Hauptablauf nicht unkontrolliert
  blockieren.

## Stabiler Debugging-Ausgangspunkt

- Für die erste Symptomklassifikation `.agents/DEBUGGING_CACHE.md` verwenden;
  der ausführliche schichtorientierte Ablauf steht in
  `docs/debugging/MODULE_DEBUGGING.md`.

- Deployment-/Update-Primärdoku: `docs/deployment/DEPLOYMENT.md` und
  `docs/debugging/2026-08-04-update-path-review.md`.
- Bekannte Produktionsfehler und geprüfte Ursachen:
  `docs/debugging/DEPLOYMENT_INCIDENTS.md`. Dort zuerst nach Symptom suchen,
  bevor Logs oder Abläufe erneut vollständig kartiert werden.
- Produktionslogs tokenarm mit `infrastructure/scripts/diagnostics/debug.sh` am Ursprung sammeln. Bereich,
  Kategorie, Zeitraum, Zeilenlimit und optionalen Suchtext eng wählen. Der
  Remote-Collector schreibt nichts auf das Ziel; nur die redigierte lokale Datei
  unter `.diagnostics/` für Agentenanalyse öffnen. Rohlogs nicht übernehmen.
- API-Fehler werden zentral als `api_error` mit Status, Methode, Pfad und
  ausnahmebezogener Ursache protokolliert; keine Request-Payloads oder Secrets in
  Logs ergänzen. Sicherheitsablehnungen bleiben separat als `security_401` bzw.
  `security_403` sichtbar.
- Bei 500ern aus Kalender oder Staff-Datumsfiltern zuerst auf
  `MethodArgumentTypeMismatchException` prüfen. OpenAPI-`date` und `date-time`
  müssen im Routengenerator explizit als ISO gebunden werden; Browser-UTC-Werte
  tragen `Z`. Transport-Bindungsfehler sind HTTP 400, keine Serverfehler.
- Master-Data-`UnrecognizedPropertyException` auf `seed_checksum`, relationale
  IDs oder Hilfsspalten bedeutet, dass interne Datenbankfelder ungefiltert an
  den API-Contract gelangten. Am Mapper-Rand entfernen, nicht den öffentlichen
  Contract erweitern oder Jackson global lockern.
- Security-Dashboard-`ClassCastException` zwischen `java.sql.Date` und
  `LocalDate` am Persistence-Rand über `RowValues.date` normalisieren.
- Gateway-`stat()`-Fehler auf dem Maintenance-Marker weisen auf die fehlende
  zusätzliche Runtime-Gruppe 10001 hin; Status bleibt read-only, Rechte nicht
  pauschal öffnen.
- Der Release-Ablauf hält PostgreSQL-Daten unter dem gemeinsamen Installationsroot,
  erstellt vor Updates koordinierte Backups, lässt Flyway migrieren und stellt bei
  fehlgeschlagener Aktivierung Release und Backup wieder her. Niemals Volumes oder
  Datenverzeichnisse als vermeintliche Fehlerbehebung löschen.
- Das Cookie-Consent-UI öffnet ohne gespeicherte Entscheidung nicht automatisch,
  solange keine optionale Cookie-/Tracking-Integration aktiv ist. Manuelles Öffnen
  bleibt über Footer und Datenschutzcenter möglich.
- API-Nutzung und Sicherheitsgrenzen stehen in `docs/reference/API.md`; der
  vollständige Endpunktindex wird aus `openapi/openapi.json` nach
  `docs/reference/API_ENDPOINTS.md` generiert.
- Historische Audit-Snapshots werden nicht mehr als zweite Dokumentationsquelle
  gepflegt. Aktuelle Soll-Regeln stehen ausschließlich in Architektur-,
  Entwicklungs-, Referenz- und Betriebsdokumenten.

## Release-Regel

Jeder deploybare Stand erhält eine neue Version. Fehlerfixes ohne höhere
Änderungsklasse erhöhen mindestens `PATCH` um `0.0.1`; aktivierte Versionen werden
nie wiederverwendet. Die aktuelle Basis immer aus `VERSION` lesen.

## Häufige Befehle

```bash
make test          # schneller, ggf. Toolchains überspringender Prüfpfad
make validate      # vollständiges Release-Gate; identisch zu make test-full
make spring-test   # Maven verify
make sql-audit     # statischer SQL-Fragment-/Parameter-/Schema-Audit
make frontend-test # Frontend-Test, Produktionsbuild und Chromium-Smokes
make check-tree    # strikte Repository-Hygiene
make build         # Spring-Paket plus Frontend-Build
make package-release
```

Vor `make validate` beziehungsweise einem direkten
`infrastructure/scripts/quality/validate.sh`-Lauf wird
die kleine, fest versionierte Python-Testsuite einmalig mit
`python3 -m pip install -r requirements-ci.txt` installiert. Die CI- und
Release-Workflows tun dies nach `actions/setup-python` explizit; gehostete
Python-Runtimes bringen `pytest` nicht verlässlich mit.

Agenten-Helfer für wiederkehrende Bestandsaufnahme und Prüfauswahl:

```bash
bash .agents/scripts/project-context.sh       # kompakter, stets aktueller Projekt-/Git-Snapshot
bash .agents/scripts/check-changes.sh         # Prüfempfehlung aus den geänderten Pfaden
bash .agents/scripts/check-changes.sh --run   # empfohlene vorhandene Repository-Gates ausführen
bash .agents/scripts/check-backend.sh         # SQL-Runtime-Audit + Maven/PostgreSQL, kompakte Ausgabe
bash .agents/scripts/check-frontend.sh        # Frontend-Test/Build/Browser-Smoke mit temporärer .env
bash .agents/scripts/check-infrastructure.sh  # Infrastruktur-/Update-Verträge, kompakte Ausgabe
bash .agents/scripts/check-docs.sh            # lokale Markdown-Links, Befehle und Doku-Generierung
bash .agents/scripts/check-cache.sh           # Modulbestand in Primärdoku und Quick-Cache abgleichen
bash .agents/scripts/check-all.sh             # make validate mit kompakter Ausgabe
```

Die Helfer enthalten keine eigene Fachprüfung. Sie lesen den aktuellen Stand und
delegieren an `make` und `infrastructure/scripts/quality/`, damit keine zweite,
später abweichende Qualitätslogik entsteht. Dokumentationsinvarianten liegen in
`infrastructure/scripts/quality/check_documentation.py`; `check-docs.sh` ist nur
der tokenarme Einstieg. Erfolgreiche Gates liefern eine Statuszeile, Fehler die
letzten 200 Logzeilen. `AGENT_GATE_VERBOSE=1` schaltet die vollständige Ausgabe
für gezielte Diagnose ein.

Lang laufende Gates, Downloads und Container-Builds bleiben in ihrer bestehenden
Prozess-Session aktiv. Zur Tokenschonung nicht eng pollen oder wiederholt
Vollausgaben anfordern, sondern bis zum Abschluss beziehungsweise bis zu einem
handlungsrelevanten Fehler warten und erst dann mit dem Ergebnis weiterarbeiten.
Fehlende Zwischenausgabe ist kein Grund, denselben Prozess erneut zu starten.

Der OWASP-Dependency-Check lädt bei leerem Cache mehrere hunderttausend
NVD-Datensätze. Einen keylosen Cold Start nicht lokal bis zum Ende babysitten:
Nach dem erfolgreichen Verbindungs- und Konfigurationsnachweis den lokalen Lauf
beenden und den verpflichtenden vollständigen Scan im GitHub-Security-Workflow
mit Maven-Cache sowie vorzugsweise dem optionalen Secret `NVD_API_KEY` ausführen.
Das Secret wird nur bei nicht leerem Wert als Umgebungsvariable an den Scanner
übergeben; der Cache beschleunigt den Lauf, ersetzt aber niemals das Scan-Gate.
`gh secret set NVD_API_KEY` ändert GitHub-Konfiguration und benötigt keinen
Commit oder Trigger-Push. Danach `gh workflow run security.yml` auslösen oder
einen bekannten fehlgeschlagenen Lauf mit `gh run rerun <run-id> --failed`
wiederholen. Der neue Lauf liest den aktuell gespeicherten Secret-Wert; niemals
versuchen, den Schlüssel zur Kontrolle auszugeben.

Der Security-Workflow läuft bei jedem Push nach `main` und beansprucht dabei den
NVD-Dienst. Deshalb Änderungen lokal in sinnvollen, geprüften Commits sichern,
Pushes aber als separate bewusste Aktion bündeln. Nicht nach jedem kleinen Commit
pushen und keinen Push nur als NVD-Key- oder Cache-Test erzeugen; bei gezieltem
Bedarf den vorhandenen Workflow manuell starten beziehungsweise fehlgeschlagene
Jobs erneut ausführen.

Trivy prüft API und Gateway in aufeinanderfolgenden fail-closed Schritten. Ein
Fund im API-Image verhindert daher den nachfolgenden Gateway-Schritt. Nach einem
Container-Sicherheitsfix lokal immer beide fertig gebauten Images separat mit
demselben Trivy-Cache scannen; der Java-Scan lädt beim ersten Lauf eine große
zusätzliche Datenbank. Die Runtime-Dockerfiles müssen vor dem Wechsel zum
unprivilegierten Benutzer `apk upgrade --no-cache` ausführen.

Der Security-Scan vom 5. August 2026 erforderte gezielte Spring-Boot-
Dependency-Overrides: Tomcat `11.0.24` für die bis `11.0.23` reichenden
Juli-Fixes, Log4j `2.25.5` für `CVE-2026-49844` und pgJDBC `42.7.12` für
`CVE-2026-54291`. Diese Werte sind in `pom.xml` und `security_audit.py` als
gemeinsam zu aktualisierender geprüfter Stand gebunden; neue Scannerfunde zuerst
gegen die Herstellerhinweise prüfen und nicht pauschal unterdrücken.

`infrastructure/scripts/quality/validate.sh full` führt statische Repository-, Security-, Spring-, SQL-Runtime- und
CSS-Audits, Java-Syntaxprüfung, Infrastruktur-/Update-Tests, Recovery-Pytests,
`mvn verify`, Frontend-Tests/Build/Chromium-Smokes und abschließend `--strict-tree`
aus. Playwright-Chromium wird lokal einmalig mit `npx playwright install chromium`
im `frontend/` installiert. Für kleine
Änderungen zuerst gezielt testen, danach die betroffenen Gates; bei
querschnittlichen Änderungen `make validate`.

## Änderungs-Checklisten

### API oder Backend-Domäne

1. OpenAPI-Operation, API-DTO, Modul-Controller, Service,
   Repository/Mapper, Security und Audit gemeinsam verfolgen.
2. Erfolgs-, Fehler- und Berechtigungsfälle ergänzen; bei Listen auch Filter,
   Grenzwerte und Query-Anzahl prüfen.
3. Für Review-/Admin-/State-Machine-Endpunkte einen stateful HTTP-Lifecycle testen:
   Voraussetzung erzeugen -> Listen/Detail lesen -> Transition -> Folge-Read; alternative
   Entscheidungen getrennt und verbrauchte Transition als kontrolliertes 4xx prüfen.
   `ApiSurfaceIntegrationTest`, SQL-Audit und Lifecycle-Test sind komplementär.
4. Keine PII, Tokens, vollständigen IP-Adressen oder Secrets in Logs, Fehlern,
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
`pom.xml`, `package.json`, `Makefile`, `infrastructure/scripts/quality/validate.sh`, Modulverzeichnisse oder
Runtime-/Deployment-Topologie geändert wurden. Keine flüchtigen Dateizahlen,
Testzahlen oder Vertragsoperationszahlen als Entscheidungsgrundlage verwenden;
bei Bedarf direkt mit `rg`, `find` oder dem jeweiligen Parser ermitteln.
Für den flüchtigen Stand zuerst `bash .agents/scripts/project-context.sh` ausführen;
dadurch müssen Branch, Version, Arbeitsbaum und Debugging-Einstiege nicht aus
älteren Sitzungszusammenfassungen rekonstruiert werden.
`project-context.sh` meldet außerdem `agent_cache_status`; bei `stale` zuerst
`bash .agents/scripts/check-cache.sh` ausführen und die fehlenden Einträge
fachlich ergänzen. Ein grüner Check beweist Bestandsvollständigkeit, nicht die
inhaltliche Aktualität der Beschreibung.

### Daily dependency cache check and CVE-2026-66299 suppression

Security dependency analysis is intentionally **daily**, not weekly. `.github/workflows/security.yml` refreshes the OWASP Dependency-Check vulnerability cache first (`dependency-check:update-only`, `nvdValidForHours=0`) and then runs the scan with automatic updating disabled so the analyzed dataset is exactly the refreshed cache. The date-scoped cache under `~/.m2/repository/org/owasp/dependency-check-data` prevents repeated cold NVD imports while still producing a fresh daily cache generation.

`spring-api/dependency-check-suppressions.xml` currently contains one reviewed exception for `CVE-2026-66299` and **only** `pkg:maven/org.apache.tomcat.embed/tomcat-embed-core@11.0.24`. Reason: Apache limits the vulnerability to the WebSocket chat example application; the WoSB Spring Boot runtime embeds Tomcat and does not ship Tomcat's examples webapp. This is an applicability exception, not an acceptance of a vulnerable deployed component.

Removal is mandatory when one of these conditions is reached:
1. Spring Boot / dependency management resolves embedded Tomcat to **>= 11.0.25**;
2. Apache changes the advisory so non-example embedded deployments are affected;
3. the suppression reaches its hard expiry on **2026-09-08 UTC**.

The security workflow sets `failBuildOnUnusedSuppressionRule=true`. Therefore a dependency upgrade that fixes/removes the finding deliberately turns this suppression into a CI failure until the rule is deleted. Agents must **remove** an unused suppression, not weaken that check. Extending the expiry requires a fresh upstream advisory review and an updated explanation in both `.agents/` and `docs/development/TESTING.md`.

### 2026-08-08 security/TLS backlog closure

The former `.agents/ToDo.txt` security items are closed as enforced invariants. Test is the default origin target; Production requires `--production`, and the selected runtime receives `DEPLOYMENT_ENVIRONMENT`. Production must use a public hostname, `TLS_MODE=letsencrypt` and `LETSENCRYPT_STAGING=false`; test may use staging/self-signed. Never copy certificates from test to production: each target owns `shared/data/{certs,letsencrypt}` and obtains its own certificate. `sync-certificate.sh` validates hostname, key pairing and remaining lifetime before atomic replacement.

Release PostgreSQL is no longer host-published. Uploads are bounded at gateway, Spring multipart and service quota/type/signature layers. Frontend route guards and upload checks are defense-in-depth only; backend authorization and validation remain authoritative. Update activation still requires coordinated pre-deployment backups and restores the previous release/data on failed activation. Debug API 500s through the stateful HTTP integration suites and SQL runtime audit rather than ad-hoc production container sessions.
### 2026-08-08 deployment-host quality-tool portability

Mandatory `update.sh`/deployment quality gates must not depend on optional developer utilities. In particular, TLS/environment safety checks use baseline `grep` plus `openssl`; `ripgrep` (`rg`) is not a deployment-host prerequisite. If a new mandatory gate needs an external command, either declare/install it explicitly as an infrastructure prerequisite or implement the check with the existing baseline toolset.
