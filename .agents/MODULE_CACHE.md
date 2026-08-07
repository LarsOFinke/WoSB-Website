# Cached Quick Overview – Module

Dieser Cache ist der schnelle Routing-Layer für Agenten. Fachlich verbindlich ist
der [Modulkatalog](../docs/architecture/MODULE_CATALOG.md), anschließend der
betroffene Quellcode. `bash .agents/scripts/check-cache.sh` stellt sicher, dass
kein Modulverzeichnis in Docs oder Cache fehlt; es bewertet nicht die inhaltliche
Richtigkeit einer Beschreibung.

## Backend in einem Blick

| Pfad | Kurzverantwortung | Erster Prüfpunkt |
| --- | --- | --- |
| `spring-api/src/main/java/eu/royalblackwater/api/account/` | Auth, Session, Profil, Registrierung, Admin-Seed | `AuthService`, Bootstrap-/HTTP-Tests |
| `spring-api/src/main/java/eu/royalblackwater/api/audit/` | datensparsames Änderungs-Audit | `AuditService`, Entität/Aktion/Feldliste |
| `spring-api/src/main/java/eu/royalblackwater/api/builds/` | Build-Persistenz, Validierung, Berechnung, Druck | Calculator-/Contracttests |
| `spring-api/src/main/java/eu/royalblackwater/api/calendar/` | Kalender und Events | ISO-Datumsbindung, `CalendarService` |
| `spring-api/src/main/java/eu/royalblackwater/api/config/` | Composition, Properties, Security, Errors | `application.yml`, Start-/Bindingfehler |
| `spring-api/src/main/java/eu/royalblackwater/api/content/` | sichere Content-Embeds | Validator plus Aufrufer |
| `spring-api/src/main/java/eu/royalblackwater/api/dto/` | generierte HTTP-DTOs | `openapi/openapi.json` + DTO-Generator, nie direkt editieren |
| `spring-api/src/main/java/eu/royalblackwater/api/core/` | Health/Readiness/Kernoperationen | Health plus DB/Flyway |
| `spring-api/src/main/java/eu/royalblackwater/api/files/` | Upload, Quoten, Typen, Eigentum | Storage-/Pfadgrenzen |
| `spring-api/src/main/java/eu/royalblackwater/api/fleet/` | Flotte, Memberships, Rollen/Fähigkeiten | AccessPolicy und Bootstrap-Membership |
| `spring-api/src/main/java/eu/royalblackwater/api/forum/` | Threads, Posts, Attachments | Eigentum/Moderation |
| `spring-api/src/main/java/eu/royalblackwater/api/groups/` | Gruppen und Mitglieder | `GroupService` |
| `spring-api/src/main/java/eu/royalblackwater/api/guides/` | Guides, Referenzen, Markdown | Service plus Print/Sanitizing |
| `spring-api/src/main/java/eu/royalblackwater/api/legal/` | Impressum öffentlich/admin | Publish-Status und Properties |
| `spring-api/src/main/java/eu/royalblackwater/api/masterdata/` | Seed, Overrides, Stammdaten | Seeder-/Mapper-/PostgreSQL-Tests |
| `spring-api/src/main/java/eu/royalblackwater/api/onboarding/` | Newcomer-Guide | Blocksortierung/Embed-Validierung |
| `spring-api/src/main/java/eu/royalblackwater/api/operations/` | Backup-/Update-Inbox | Control-Datei und Host-Runner |
| `spring-api/src/main/java/eu/royalblackwater/api/persistence/` | JDBC-/Typ-Helfer | Nullparameter und `RowValues` |
| `spring-api/src/main/java/eu/royalblackwater/api/privacy/` | Consent, Export, Anträge, Löschung/Retention | `PrivacyIntegrationTest`, keine Schlüssel loggen |
| `spring-api/src/main/java/eu/royalblackwater/api/raidhelper/` | externe Eventzustellung | Policy, Worker, Deliverystatus |
| `spring-api/src/main/java/eu/royalblackwater/api/security/` | Session, CSRF, Host/Origin, Kryptografie | 401/403/CSRF separat prüfen |
| `spring-api/src/main/java/eu/royalblackwater/api/securityops/` | Sperrsignale/IP-Blocks/Dashboard | Aggregation, `RowValues.date` |
| `spring-api/src/main/java/eu/royalblackwater/api/shared/` | gemeinsame Web-/Filter-/Mapper-Helfer | keine Fachlogik, mehrere Verbraucher |
| `spring-api/src/main/java/eu/royalblackwater/api/ships/` | lesender Schiffskatalog | Query/Filter/Taxonomie |
| `spring-api/src/main/java/eu/royalblackwater/api/squads/` | Squad/Roster auf Fleet-Membership | Fleet-ID, Status, Capability |
| `spring-api/src/main/java/eu/royalblackwater/api/webhooks/` | Webhook-Policy und Zustellung | Scope/Event/verschlüsseltes Secret |

## Frontend in einem Blick

Für alle Featuremodule gilt: `page -> composable -> api/domain`; Fehlerzustand im
Composable, nicht in der Seite diagnostizieren.

| Pfad | Kurzverantwortung | Erster Prüfpunkt |
| --- | --- | --- |
| `frontend/src/modules/accounts/` | Login, Registrierung, Profil, Privacy-Self-Service | Session/Redirect/Composable |
| `frontend/src/modules/admin/` | Staff-/Admin-Arbeitsbereiche | aktiver Sub-Composable und Rollenmetadaten |
| `frontend/src/modules/builds/` | Bibliothek, Designer, Berechnung, Druck | reine Domain-/Contracttests |
| `frontend/src/modules/calendar/` | Kalender/Eventerstellung | UTC-Payload und Grid |
| `frontend/src/modules/combat/` | lokale DPM-Analyse | Domainberechnung ohne Tipp-Requests |
| `frontend/src/modules/files/` | Datei-API und Client-Typen | Uploadstatus, Backend bleibt autoritativ |
| `frontend/src/modules/fleet/` | Landing, öffentlich, Verwaltung | Backend-Capabilities/Responsive |
| `frontend/src/modules/forum/` | Threads/Posts | Composable, Eigentum, Bestätigung |
| `frontend/src/modules/groups/` | Gruppenworkflows | Domain vs. Zustand trennen |
| `frontend/src/modules/guides/` | Suche, Editor, Reader, Print | Sanitizing/Presentation/Responsive |
| `frontend/src/modules/legal/` | Impressum und Editor | Publish-Status/Locale |
| `frontend/src/modules/onboarding/` | Newcomer-Guide | Draft-/Ressourcenregeln |
| `frontend/src/modules/privacy/` | Privacy-Center/Cookie-Banner | Retry, Payload, Fehler bleibt sichtbar |
| `frontend/src/modules/ships/` | Schiffskatalog-Transport | Verbraucher in Builds/Combat |
| `frontend/src/modules/squads/` | Listen, eigene Squads, Roster | Membership-ID/Managementregeln |

Gemeinsame Bereiche: `frontend/src/assets/`, `frontend/src/config/`,
`frontend/src/core/`, `frontend/src/locales/`, `frontend/src/router/`,
`frontend/src/shared/` und `frontend/src/styles/`. Änderungen sind meist
querschnittlich; Locale-Ausgaben und `dist/` bleiben generiert.

## Infrastruktur in einem Blick

| Pfad | Kurzverantwortung | Sicherer Einstieg |
| --- | --- | --- |
| `infrastructure/scripts/backup/` | Backup und Retention | Backup-/Recovery-Vertrag |
| `infrastructure/scripts/checks/` | Readiness/Doctor | read-only prüfen |
| `infrastructure/scripts/deployment/` | Zielinstallation/Aktivierung | Failed-Activation-Log sichern |
| `infrastructure/scripts/diagnostics/` | Remote-Sammlung/lokale Redaktion | `debug.sh --help` |
| `infrastructure/scripts/generation/` | deterministische Generatoren | jeweiliges `--check` |
| `infrastructure/scripts/lib/` | gemeinsame Shell-/Host-Helfer | direkte Aufrufer und Exitcodes |
| `infrastructure/scripts/migration/` | kontrollierte Legacy-Datenpfade | Quelle/Ziel/Recovery vorab prüfen |
| `infrastructure/scripts/quality/` | kanonische Gates/Audits | `make validate` |
| `infrastructure/scripts/release/` | Build, Transfer, Verify, Rollback | Origin-Wrapper und Artefaktmanifest |
| `infrastructure/scripts/services/` | root-owned Runtime-Runner | Inbox/Status/systemd |
| `infrastructure/scripts/setup/` | First Run | Optionen → Workflow → Composition |
| `infrastructure/scripts/tls/` | Zertifikate | Metadaten, nie private Schlüssel ausgeben |

## Cache-Regel

Bei neuem, entferntem oder umbenanntem Modul immer:

```bash
bash .agents/scripts/check-cache.sh
bash .agents/scripts/check-docs.sh
```

Der Live-Snapshot `bash .agents/scripts/project-context.sh` zeigt
`agent_cache_status=ok` oder `stale`. Ein grüner Bestandscheck ersetzt nicht die
fachliche Aktualisierung dieser Kurzbeschreibung und des Modulkatalogs.
