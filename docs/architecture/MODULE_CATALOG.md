# Modulkatalog

Dieser Katalog ist die fachliche Navigationsquelle für alle Laufzeit- und
Werkzeugmodule. Er beschreibt Verantwortung, wichtige Grenzen und den kürzesten
Diagnoseeinstieg. Einzelne Klassen und Endpunkte bleiben im Quellcode und in der
[API-Referenz](../reference/API.md) verbindlich; dieser Katalog ersetzt keine
Detailanalyse des betroffenen Ablaufs.

Neue Verzeichnisse unter den drei katalogisierten Modulwurzeln müssen hier und im
[Agenten-Modulcache](../../.agents/MODULE_CACHE.md) ergänzt werden. Das
Dokumentationsgate gleicht beide Bestände automatisch mit dem Dateisystem ab.

## Backend-Module

Alle Backendmodule liegen unter
`spring-api/src/main/java/eu/royalblackwater/api/`. Der normale Ablauf ist
OpenAPI-Spezifikation → generiertes API-DTO → Modul-Controller → Service →
Repository/Mapper → API-/Modul-DTO. Bei API-Fehlern zuerst Route/`operationId`,
Controller, Service und serverseitige Berechtigungsentscheidung zusammen verfolgen.
Die Spring-MVC-Bindings liegen direkt im Controller und werden gegen OpenAPI auditiert.

| Modul | Verantwortung und Grenzen | Diagnose und zentrale Tests |
| --- | --- | --- |
| `spring-api/src/main/java/eu/royalblackwater/api/account/` | Login, Sessions, Profile, Registrierung, Benutzerverwaltung und Bootstrap-Admin. Passwörter und Sessiontokens verlassen den Sicherheitsrand nicht. | `AuthService`, `BootstrapAdministratorInitializer`, `ApplicationIntegrationTest`; bei 401 zuerst `security_401` und Session-/Rollen-Fetch prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/audit/` | Datensparsame Historie administrativer Änderungen. Audittexte enthalten keine Payloads, Secrets oder vollständigen IP-Adressen. | `AuditService`, `AuditLogQueryService`; Entitätstyp, Akteur und geänderte Feldnamen prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/builds/` | Build-Katalog, Validierung, Berechnung, Rollen, Votes und Druckausgabe. Berechnung und Persistenz bleiben getrennt. | `BuildStatCalculatorTest`, Contract-Fixtures und Build-API-Regressionen; bei 500 Mapper- und Katalog-Snapshots prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/calendar/` | Flotten-/Squad-Kalender und Eventzugriff; Raid-Helper-Zustellung bleibt eine nachgelagerte Integration. | `CalendarService`; ISO-`date`/`date-time`-Bindung und `MethodArgumentTypeMismatchException` prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/config/` | Spring-Komposition, typisierte Konfiguration, Security- und Fehlergrenzen, Scheduling. Keine Fachlogik. | `application.yml`, `SecurityConfiguration`, `ApiExceptionHandler`; Bindingfehler beim Start und zentrale `api_error`-Zeilen prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/content/` | Gemeinsame Validierung sicher eingebetteter Inhalte. | `ContentEmbedValidator` und aufrufende Guides-/Forum-Services; abgelehnte Schemes und Hosts gezielt testen. |
| `spring-api/src/main/java/eu/royalblackwater/api/dto/` | Generierte Request-/Response-DTOs des HTTP-Vertrags. Fachmodulinterne Übergabe-DTOs liegen separat unter `<domain>/dto`. | DTO-Generator, Contract-Schema und DTO-Grenzprüfungen im Spring-Audit. |
| `spring-api/src/main/java/eu/royalblackwater/api/core/` | Kleine, domänenübergreifende Kernoperationen wie Health/Readiness in Controller, Service und Repository getrennt. | `CoreController`, `CoreService` und `/api/health*`; bei Readiness zusätzlich DB und Flyway prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/files/` | Upload, Inhaltsabruf, Quoten, Typ- und Eigentumsprüfung. Metadaten liegen in PostgreSQL, Binärdaten im konfigurierten Storage. | `FileAssetService`, Storage-Konfiguration und Upload-Grenztests; Pfadnormalisierung und freien Speicher prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/fleet/` | Flotten, Rollen, Mitgliedschaften, Führung und serverseitige Fähigkeiten. Bootstrap-Flottenleitung wird durch die Account-Initialisierung sichergestellt. | `FleetAccessPolicyTest`, `BootstrapAdministratorInitializerTest`, HTTP-Squad-Test; Rollen-Code, Status und Fleet-ID gemeinsam prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/forum/` | Threads, Beiträge, Anhänge, Eigentümer- und Moderationsoperationen. | `ForumService` und Frontend-Forumtests; bei Löschung Referenzen und Berechtigung getrennt prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/groups/` | Nutzergruppen, Mitgliedschaften, Rollen und Beitrittsabläufe außerhalb der offiziellen Flotte. | `GroupService`, Gruppen-Composables und echte Benutzerreferenzen prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/guides/` | Guide-Erstellung, Darstellung, Anhänge, Build-Referenzen und Administration. | `GuideService`, Markdown-/Printtests; Rich-Text-Sanitizing und Eigentum prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/legal/` | Veröffentlichbares Impressum und administrativer Entwurf aus typisierter Konfiguration/Persistenz. | `LegalNoticeService`, `docs/reference/LEGAL_NOTICE.md`, öffentliche und Admin-Sicht getrennt testen. |
| `spring-api/src/main/java/eu/royalblackwater/api/masterdata/` | Seed-Katalog, idempotente Synchronisierung, lokale Overrides und administrative Stammdatenpflege. Interne Seed-Metadaten sind kein API-Vertrag. | `SeedCatalogTest`, `MasterDataQueryServiceTest`, PostgreSQL-Integration; bei `UnrecognizedPropertyException` Mapper-Rand prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/onboarding/` | Strukturierter Newcomer-Guide mit Seiten, Blöcken und sicheren Ressourcen. | `NewcomerGuideService` und Frontend-Drafttests; Sortierung und Embed-Validierung prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/operations/` | Unprivilegierte API für Backup-/Update-Anforderungen über kontrollierte Inbox-Dateien. Führt keine Hostbefehle aus. | `ControlFileStore`, Operations-Integration und systemd-Runner; Statusdatei, Request-ID und Dateirechte prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/persistence/` | Gemeinsame JDBC-Abfragen, Nullparameter und sichere Typkonvertierung. Keine domänenspezifischen Queries sammeln. | `JdbcQueryService`, `RowValues`, `SqlParameters`; JDBC-/Java-Typen am Rand normalisieren. |
| `spring-api/src/main/java/eu/royalblackwater/api/privacy/` | Cookie-Consent, Kontaktpostfach, Datenexport, Betroffenenanträge, Pseudonymisierung und Aufbewahrung. Keine IP/User-Agent-Erfassung im Kontaktworkflow. | `CookieConsentServiceTest`, `PrivacyServiceTest`, `PrivacyIntegrationTest`, [Aufbewahrung](../reference/DATA_RETENTION.md); Consent-Key nie ausgeben. |
| `spring-api/src/main/java/eu/royalblackwater/api/raidhelper/` | Profile, Ziele, Templates, Payload-Rendering und verzögerte externe Zustellung. Fehler dürfen den Kalenderablauf nicht unkontrolliert blockieren. | `RaidHelperDeliveryWorker`, Probe-/Policy-Services und [Integrationsreferenz](../reference/RAID_HELPER_CALENDAR.md). |
| `spring-api/src/main/java/eu/royalblackwater/api/security/` | Authenticated Principal, Sessionfilter, CSRF, Passwort- und Secret-Kryptografie sowie Host-/Origin-Grenze. | Security-Unit-Tests und `ApplicationIntegrationTest`; 401, 403 und CSRF getrennt diagnostizieren. |
| `spring-api/src/main/java/eu/royalblackwater/api/securityops/` | Zweckgebundene aggregierte Sperrsignale, IP-Sperren und Security-Dashboard. Keine allgemeine Requesthistorie. | `SecurityDashboardServiceTest`, [Aufbewahrung](../reference/DATA_RETENTION.md); JDBC-`DATE` über `RowValues` lesen. |
| `spring-api/src/main/java/eu/royalblackwater/api/shared/` | Schmale modulübergreifende Web-, Filter- und Mapping-Helfer ohne Fachlogik. | `ApiControllerSupport`, `ListFilter`; neue Helfer nur bei mehreren echten Verbrauchern und ohne Fachlogik. |
| `spring-api/src/main/java/eu/royalblackwater/api/ships/` | Lesender Schiffskatalog, Waffenklassen, Mounts und Leistungsprofile. Mutationen laufen über Stammdaten. | `ShipQueryService`, Listenfilter und Master-Data-Seedtests; Taxonomie-IDs und aktive Datensätze prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/squads/` | Squads innerhalb einer Flotte, Roster, Rollen, Leitung und Mitgliedschaften auf Basis gültiger Fleet-Memberships. | `SquadAccessPolicyTest` und PostgreSQL-HTTP-Test; Fleet-Zugehörigkeit, Membership-Status und Rollenfähigkeit gemeinsam prüfen. |
| `spring-api/src/main/java/eu/royalblackwater/api/webhooks/` | Website-Webhooks, Eventkatalog, Policy, Zustellhistorie und knappe ausgehende Hinweise. Secrets bleiben verschlüsselt. | Webhook-Policy-/Payloadtests und Lieferstatus; Zielscope, Eventtyp und redigierte Fehler prüfen. |

## Frontend-Featuremodule

Featuremodule liegen unter `frontend/src/modules/`. Seiten orchestrieren,
Composables besitzen Zustand und Abläufe, API-Dateien den Transport und
Domain-Dateien reine Regeln. Ein fehlender UI-Guard ist ein UX-Fehler; echte
Berechtigungen werden ausschließlich im Backend entschieden.

| Modul | Verantwortung | Diagnose und Tests |
| --- | --- | --- |
| `frontend/src/modules/accounts/` | Login, Registrierung, Profil, Präferenzen und Datenschutz-Self-Service. | Sessionzustand, Redirect und `usePrivacySelfService`; Browser-Smokes plus Account-Domaintests. |
| `frontend/src/modules/admin/` | Gemeinsamer Staff/Admin-Workspace für Benutzer, Logs, Stammdaten, Privacy, Webhooks, Raid Helper und Operations. | Betroffenen Composable statt `AdminPage.vue` isolieren; Rollen-Sichtbarkeit, Page-Bindings und API-Status prüfen. |
| `frontend/src/modules/builds/` | Build-Bibliothek, Designer, Berechnung, Suche, Druck und Teilen. | Reine Calculation-/Domain-Tests, Contract-Fixtures, Build und Browser; Katalogladen von Eingabeänderungen trennen. |
| `frontend/src/modules/calendar/` | Kalenderansicht und Eventerstellung einschließlich expliziter Raid-Helper-Auswahl. | `calendarGrid` und Page-Composables; UTC-/Local-Date-Konvertierung und Requestpayload prüfen. |
| `frontend/src/modules/combat/` | Lokale DPM-/Panzerungsanalyse auf Basis des geladenen Katalogs. | `combatDpm`-Unit-Tests; keine API-Aufrufe pro Eingabeänderung. |
| `frontend/src/modules/files/` | Dateitransport und gemeinsame Client-Typregeln. | Uploadstatus, erlaubte Typen und Backendgrenzen; Server bleibt autoritativ. |
| `frontend/src/modules/fleet/` | Landingpage, öffentliche Flotte und Verwaltungsworkspace. | Backendgelieferte Fähigkeiten, Filter und Responsive-Tests; keine Rollen aus Namen ableiten. |
| `frontend/src/modules/forum/` | Threadliste, Erstellung, Detail, Antworten und Eigentümeraktionen. | Page-Composables, Löschbestätigung und Attachmentpfad prüfen. |
| `frontend/src/modules/groups/` | Gruppenlisten, eigene Gruppen, Erstellung, Detail und Mitgliedschaft. | `groupDetail`-Regeln und Composable-Zustände getrennt testen. |
| `frontend/src/modules/guides/` | Guide-Suche, Editor, Reader, Inhaltsverzeichnis und Druck. | Presentation-/Discovery-/Printtests, Markdown-Sanitizing und responsive Reader-Stile. |
| `frontend/src/modules/legal/` | Öffentliches Impressum und Admin-Editor. | Veröffentlichungsstatus, Textdarstellung und Rollen-Sichtbarkeit in allen Locales. |
| `frontend/src/modules/onboarding/` | Newcomer-Guide-Darstellung und administrative Ressourcenaufbereitung. | Draft-Normalisierung, sichere Ressourcen und Seitenbindung prüfen. |
| `frontend/src/modules/privacy/` | Datenschutzcenter und Cookie-Banner; fehlende Entscheidung öffnet ohne optionale Integration nicht automatisch. | `cookieConsentVisibility.test.mjs` und Browser-Smokes für Retry, Payload und Fehlerzustand. |
| `frontend/src/modules/ships/` | Schlanker lesender API-Zugriff auf Schiffsstammdaten. | Verbraucher in Builds/Combat prüfen; keine zweite Kataloglogik einführen. |
| `frontend/src/modules/squads/` | Squad-Liste, eigene Squads, Erstellung, Detail und Rosterverwaltung. | `squadManagement`, Page-Composables und Fleet-Membership-IDs im Payload prüfen. |

Die gemeinsamen Frontendbereiche `frontend/src/assets/`, `frontend/src/config/`,
`frontend/src/core/`, `frontend/src/locales/`, `frontend/src/router/`,
`frontend/src/shared/` und `frontend/src/styles/` sind keine Fachmodule. Sie
besitzen jeweils nur Assets, Laufzeitkonfiguration, App-Shell, Übersetzungen,
Routing, wiederverwendbare Bausteine beziehungsweise die globale CSS-Kaskade.
Änderungen dort sind querschnittlich und benötigen mindestens Frontend-Gate und
bei Routing/Security zusätzlich passende Backendtests.

## Infrastrukturmodule

Die Verzeichnisse unter `infrastructure/scripts/` sind nach Lebenszyklus statt
nach Dateityp getrennt. Öffentliche Root-Orchestratoren bleiben `deploy.sh` und
`update.sh`; Produktionsdiagnosen beginnen mit dem Diagnostics-Modul.

| Modul | Verantwortung und sicherer Diagnoseeinstieg |
| --- | --- |
| `infrastructure/scripts/backup/` | Konsistente PostgreSQL-/Datei-Backups, Aufbewahrung und Manifeste; mit Recovery-Vertragstests prüfen. |
| `infrastructure/scripts/checks/` | Zielseitige Readiness-/Doctor-Prüfungen ohne Reparatur durch Datenlöschung. |
| `infrastructure/scripts/deployment/` | Zielseitige Installation und Aktivierung versionierter Artefakte. Fehlgeschlagene Aktivierungsdiagnose zuerst sichern. |
| `infrastructure/scripts/diagnostics/` | Begrenzter Remote-Collector und lokale Redaktion; [Debugging-Runbook](../debugging/MODULE_DEBUGGING.md) verwenden. |
| `infrastructure/scripts/generation/` | Deterministische Generatoren für API, Java, Seed-/Buildkataloge und Referenzdoku; stets mit `--check` validieren. |
| `infrastructure/scripts/lib/` | Wiederverwendbare Shell-Helfer und Hostmodule; Aufrufer, Idempotenz und Exitcodes gemeinsam testen. |
| `infrastructure/scripts/migration/` | Kontrollierte Legacy-/Datenmigrationen außerhalb unveränderlicher Flyway-Dateien. |
| `infrastructure/scripts/quality/` | Kanonische Repository-, Security-, Dokumentations- und Full-Gates; Agentenskripte delegieren nur hierhin. |
| `infrastructure/scripts/release/` | Artefaktbau, Transfer, Verifikation, Rollback und Origin-Deployment. Keine Produktionsdaten ins Artefakt aufnehmen. |
| `infrastructure/scripts/services/` | Root-eigene Zielrunner für kontrollierte Inbox-Aktionen und Service-Lifecycle. |
| `infrastructure/scripts/setup/` | Interaktiver First Run und Host-Komposition; wiederholbar und fail-closed halten. |
| `infrastructure/scripts/tls/` | Zertifikatsbereitstellung und Erneuerung; private Schlüssel nie in Diagnose oder Repository lesen. |

## Moduländerung vollständig abschließen

1. Primärvertrag, Aufrufer, Persistenz, Konfiguration und Modulzeile dieses
   Katalogs lesen.
2. Verhalten am verantwortlichen Rand ändern und fokussierte Erfolgs-, Fehler-
   und Berechtigungstests ergänzen.
3. Den Diagnosepfad so aktualisieren, dass Fehler ohne Payloads oder Secrets
   lokalisierbar bleiben.
4. Bei neuem/umbenanntem Modul Docs und Agenten-Cache ergänzen und
   `bash .agents/scripts/check-cache.sh` ausführen.
5. Betroffene Gates und bei querschnittlicher Änderung `make validate`
   ausführen.
