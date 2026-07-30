## 2026-07-28 - Repository spring clean and security audit

- Discord webhook credentials are now stored as authenticated, versioned ciphertext with automatic plaintext migration and key rotation; deployment setup generates a database-independent key, and decrypted targets are revalidated against the Discord allowlist immediately before delivery.
- Removed the obsolete Discord avatar override from API, service, model and database; all webhook deliveries keep the public fleet icon.
- Added offline repository-specific security invariants plus OSV pull-request, main-branch and weekly dependency scans.
- Hardened GitHub checkout usage, NGINX cross-origin headers, and the read-only migration/seed container posture.
- Added a reviewed Uptime Kuma 1→2 migration runbook instead of applying an unsafe unattended major upgrade.
- Refreshed security, privacy, operations and webhook documentation and removed stale compatibility guidance.

# Changelog

## Unreleased

- Refactored the global CSS cascade around explicit layer ownership: removed retired navigation/footer selectors, consolidated exact duplicate rules, normalized responsive webhook and operation layouts, and strengthened the CSS audit against shell ownership regressions. The application footer is now owned by the shell layer, aligns with the main workspace beside the desktop sidebar, follows long content, and stays at the viewport bottom on short pages across desktop, tablet, and mobile layouts.
- Added a controlled administrator-only application restart operation to the Staff status panel. The root-side runner restarts the API and gateway in order, keeps PostgreSQL online, waits for readiness, runs smoke checks, and returns only privacy-minimal state to the website while detailed results remain in host logs and configured webhooks.
- Restricted administrator delegation to the configured bootstrap administrator: it may promote users to administrator and demote promoted administrators, while non-bootstrap administrators cannot promote or demote administrators. Migration `0015` selects an existing active administrator during upgrades, and normal seeding reconciles the capability with the configured default account.
- Reworked upload publication so client-supplied usage context no longer makes guide or forum files public. Files remain private until linked to published server-authorized content; master-data uploads require an administrator and explicit public visibility is persisted.
- Added paginated lightweight build collection responses, preserving full calculated statistics for detail views while bounding list payload and CPU cost.
- Extended remote administration backups to create, checksum, transfer and remotely verify both PostgreSQL and file-data archives, including uploads and optional certificate/Uptime Kuma data.
- Removed requester identities, commit hashes and log tails from the website update-status API and UI; detailed diagnostics remain in host logs and webhook notifications.
- Limited Raid-Helper duplicate-name handling to integrity violations while rolling back and re-raising unexpected database failures.
- Added a full-stack Chromium smoke workflow covering registration approval, login, privacy-minimal update status, and paginated build access.

- Fixed the Raid-Helper production startup failure by replacing the accidental development-only `httpx` dependency with the existing hardened outbound HTTP transport. Raid-Helper requests now reuse DNS pinning, public-address validation, TLS hostname verification and redirect blocking without adding a new runtime package.
- Added an admin-only Raid-Helper v4 calendar integration with multiple encrypted server profiles, fleet- and squad-specific channel destinations, category-filtered templates, default-on per-event delivery, create/update/cancel synchronization and visible per-target delivery status for event managers. Existing calendar webhook messages now expose normalized fleet/squad scope fields, and the Staff template editor includes matching fleet/squad presets. Migration `0014` creates the normalized profile, destination, template and event-link tables without requiring a seed.
- Added crawler load protection for the Raspberry Pi deployment: a restrictive `robots.txt`, explicit denial of declared high-volume AI training crawlers, separate per-IP limits for public pages and API traffic, connection limits, and `X-Robots-Tag` on API and authenticated workspaces.
- Fixed the Impressum administration workflow: the `.env` reset action now rereads the configured environment source instead of using only the startup cache, the default English UI consistently labels the page “Impressum”, and the application shell keeps the footer at the bottom of short pages without a viewport overlay.
- Added a public, draft-capable German legal-notice page at `/impressum` and an admin-only editor in the Staff workspace. Environment variables provide deployment defaults, while persisted administrator changes take precedence and survive updates; admins can explicitly reset the record to the currently loaded environment values. Migration `0013` creates the normalized singleton record without requiring a seed.
- Added a member-only, data-driven Combat DPM Analysis module with independent armor targets for one broadside, side-switching across both broadsides, bow and stern. Weapon damage/reload inputs now live in normalized `weapon_performance_profiles` master data, the initial 21 broadside profiles come from the supplied cannon comparison, Staff can maintain verified profiles, and missing bow/stern values are reported instead of estimated. Migration `0012` backfills existing cannon options.
- Corrected bow/stern weapon sizing: standard positional weapons now use the same normalized Light/Medium/Heavy mount ceiling as broadside cannons. Rate-7/6/5 mounts only expose Light positional weapons, Rate-4/3 mounts expose Light and Medium, and Rate-2/1 mounts expose all three classes. Friede therefore no longer receives the entire bow/stern catalogue, while the audited compatibility examples remain valid (Eagle: Basilisk/Poseidon; Azov/Deadfish: Zeus). Migration `0011` assigns the normalized weapon classes; no per-ship exceptions are introduced.
- Removed the mistaken per-ship bow/stern allowance table in migration `0010`. Positional weapons remain linked to normalized bow/rear slot types; migration `0011` adds the required Light/Medium/Heavy ceiling so availability is determined by both slot position and mount class.
- Reworked frontend stacking into one semantic z-index scale and moved Build Planner option menus into a body-level fixed popover portal. Ship, Specialist, equipment and inventory pickers now stay above the shell and every planner stacking context, reposition on viewport scroll/resize, flip above the trigger near the viewport edge, and remain below mobile drawers and modal Staff editors. Added regression checks that reject local numeric z-index values.
- Added a searchable ship picker to the Build Planner. Ship name, type and rate are filtered immediately against the already loaded ship catalog, so typing never triggers additional API requests; selection, keyboard navigation and empty-result handling reuse the existing accessible option picker.
- Corrected the Build Planner upgrade add-on to grant one data-driven upgrade slot while applying `-5%` durability, maneuverability and cargo hold. The feature and its individual effects now live in normalized database tables and Builds store only the selected feature reference. Added normalized rate-to-weapon-class rules so newly created ships receive Light weapons for rates 7–5, Medium for rates 4–3 and Heavy for rates 2–1; migration `0008` also repairs previously stored, classless regular mounts without overwriting explicit audited exceptions or touching mortar/special mounts.
- Added one-shot recovery for stale lazy-loaded frontend chunks after a server update: failed route imports now reload the requested route against the new deployment, while a per-route session guard prevents reload loops.
- Added normalized one-vote-per-user Build upvotes with vote totals in Build lists, personal lists and details; introduced moderator-managed Build-role CRUD and direct role assignment in the Staff workspace; added an in-memory Specialist picker search, corrected Build Planner dropdown stacking, and published configurable `system.update.started` / `system.update.result` webhooks with retry-safe result deduplication.
- Replaced persistent request logs with an admin-only IP-ban signal store: only the normalized IP, UTC calendar day, one coarse signal category and a daily counter are retained for seven days. Routes, query strings, user agents, request IDs, payloads, exact timestamps, status details and exceptions are no longer persisted or exposed in the Staff UI; old `app_logs` data is deliberately discarded by migration `0006`, signals are deleted as soon as an IP is blocked, client-supplied request IDs are ignored, and gateway access logs remain disabled.
- Fixed Build Print icon rendering in preview, SVG, PNG and print output by binding the browser fetch receiver correctly, embedding catalog assets before the generated SVG is used as an image, and falling back to same-origin image/canvas rasterization when direct response conversion is unavailable. Failed embedding no longer silently produces broken image placeholders. Upgrade, sail, lantern, specialist and inventory entries now use their selected catalog images without relying on external SVG resource loading.
- Discord event webhooks and manual broadcasts now always use the bundled Royal Blackwater Fleet icon. Custom avatar controls were removed from the Staff UI and legacy avatar values can no longer override the server-side payload.
- Corrected First Mate semantics: `+0.2% per Sailor` now increases sail deployment speed only, appears as its own calculated stat, and can no longer inflate base or cruise ship speed. Added the 102-Sailor Zeven regression (`14.7 kn` ship speed and `+20.4%` sail deployment speed).
- Fixed master-data seed recovery: individual restore actions are real buttons, admins can reset all repository-owned categories, options and ships from the master-data workspace, and custom records/user content remain untouched. Added `update.sh --restore-seed-defaults` for the equivalent audited server-side repair flow and explicit reporting when normal seeds preserve admin overrides.
- Completed the selectable ammunition seed catalog with Heavy Shots and Saxon Shots, stable seed IDs and translations in every supported locale.
- Audited Build Designer arithmetic end to end: De Zeven Provincien plus Raiding Sails is fixed at the verified `14.7 kn`, percentage/flat components remain dimensionally correct, and all Python/JavaScript crew and specialist rounding now uses one decimal half-up contract.
- Added a shared calculation contract and coverage gate for all 106 numeric seed-effect keys.
- Added Discord website-webhook events and versioned templates for group-search creation, joins and closure; fleet-scoped delivery follows the listing owner and payloads omit contact/member notes.

- Fixed a deployment deadlock where seed or migration updates invoked `backup-all.sh` while already holding `update.lock`; update backups now reuse the existing update lock and acquire only `backup.lock`.

### Owned-ship seed audit

- Re-audited 38 owned ships from 230 current in-game screenshots, adding 12 Apostolov, Balloon, Flying Cloud, Huracan and La Royale to the prior owned batch and updating their displayed cruise-speed maxima.
- Added sparse screenshot-backed upgrade values for 28 ships, including the newly verified 12 Apostolov, Flying Cloud, Huracan and La Royale combat exceptions while preserving inherited global effects for all unlisted values.
- Ship master-data edits now synchronize existing sparse upgrade rows in place, preventing uniqueness conflicts when administrators edit ships that already have seeded overrides.
- Corrected the global Teak Frames armor value from `15` to `1.5`.
- Extended the JSON seed schema and bootstrap so ship-specific upgrade values resolve by stable upgrade IDs, survive normal reseeds and are restored by the master-data admin workflow.
- Documented account-level upgrade-slot handling and retained ambiguous mortar layouts until quantified modification panels are available.
- Corrected Balloon to zero upgrade slots from its explicit `Upgrades -` panel and prevented research or expansion effects from creating a rack on rackless ships.

### Repository spring clean and privacy hardening

- Split the historical 11,466-line global stylesheet into eight deterministic JavaScript-imported cascade layers with budgets and a standalone CSS audit.
- Reused one presentational filter surface across the staff workspace and documented KISS/SOLID boundaries.
- Replaced nested full user profiles with minimal identity references in shared content APIs.
- Redacted reviewed registration password hashes and all request query values.
- Added configurable retention for webhook deliveries, cookie consent history, and registration requests.
- Added a security/privacy audit and operational data-retention documentation.
- Split webhook event metadata, samples, and templates behind a thin compatibility facade.
- Made the locale completeness check directly executable with Node instead of requiring a Vite server.
- Pinned GitHub workflows to the published v6 releases of checkout, setup-node, setup-python, and upload-artifact.

- Admin-exklusive Datenbank-Backup-Verwaltung ergänzt: SSH-/SFTP-Ziel inklusive verifizierter Host-Key-Pinierung über die Webseite einrichten, Verbindung testen und komprimierte PostgreSQL-Backups per Knopfdruck übertragen sowie remote per SHA-256 verifizieren. Private Schlüssel verbleiben im root-geschützten Host-Control-Verzeichnis und werden nie von der API zurückgegeben.
- Frontend-Release-Gate repariert: vollständige Übersetzungen für die neue Broadcast-Navigation ergänzt und die Route-Page-Invarianten an die Backup-Unterseite angepasst; GitHub Actions auf veröffentlichte, runner-kompatible Major-Versionen zurückgeführt.
- Discord-Verwaltung fachlich getrennt: automatische Website-Webhooks bleiben unter „Discord-Webhooks“, während externe Partnerflotten- und Diplomatieziele eine eigene Broadcast-Unterseite erhalten; der Zustellmonitor ist standardmäßig eingeklappt und seine Historie kann einzeln oder gefiltert gelöscht werden.
- Forum-Antworten können nach Inline-Bestätigung durch Autor oder Staff gelöscht werden; neue Webhook-Events und versionierte Templates decken Antworten, Thread-Löschungen sowie Flotten-, Mitgliedschafts-, Führungs- und Rollenänderungen ab.
- Staff-Systemlogs in einen eigenen responsiven Arbeitsbereich ausgelagert; aktive IP-Sperren werden standardmäßig aus Liste, Kennzahlen und Threat-Auswertung entfernt und können bewusst wieder eingeblendet werden. Admins können einzelne oder den aktuellen Filterbereich nach Bestätigung löschen; jede Löschung bleibt im Audit-Log nachvollziehbar.
- Alle Route-Pages auf verbindliche Page-Composables umgestellt; direkte API-Imports, Lifecycle-Ladevorgänge und eigene asynchrone Workflows in Seiten werden repositoryweit verhindert.
- Globales Frontend-CSS unter Beibehaltung der Kaskadenreihenfolge in acht größenbegrenzte Layer zerlegt und mit CSS-Budgets abgesichert.
- Python-, Node-, NGINX-, PostgreSQL- und Uptime-Kuma-Basisimages auf konkrete Versionen festgeschrieben; unversioniertes pip-Self-Upgrade aus dem Backend-Build entfernt.
- Upload-Auslieferung durch API-Zugriffspolitik und private No-Store-Header gehärtet: Guide-, Forum- und Master-Data-Dateien bleiben öffentlich, sonstige Dateien sind auf Eigentümer und Staff begrenzt; bestehende `/uploads/...`-Links bleiben kompatibel.
- Build-Editor um eine abgesicherte Löschaktion für eigene Builds ergänzt; nach Bestätigung wird der Build entfernt und zur persönlichen Build-Bibliothek zurück navigiert.
- Discord-Webhook-Editor als isolierten, responsiven Body-Drawer umgesetzt; Checkboxen, Formularelemente und Aktionen überlagern sich nicht mehr, der Hintergrund wird während der Bearbeitung gesperrt.
- Webhook-Zustellungen atomar beansprucht und um automatische Wiederaufnahme verwaister `queued`-/`processing`-Einträge mit begrenzten Versuchen ergänzt.
- Produktionslogging gibt strukturierte Meldungen zusätzlich auf der Konsole aus, damit Datenbankausfälle nicht gleichzeitig die Laufzeitdiagnose abschalten.
- Release-Prüfungen gegen plattformabhängige Zeilenenden und einen veralteten Alembic-Head gehärtet; mehrere testreihenfolgeabhängige Fixtures korrigiert.
- Ursprüngliche Upload-Dateinamen werden vor der Persistierung auf die Datenbankgrenze gekürzt.
- Webhook-Template-Autofill und Backend-Standardnachrichten verwenden nun exakt die vollständigen englischen Repository-Templates mit Kontextfeldern und Deep-Links; eine Release-Invariante verhindert erneute Abweichungen.
- Staff-Overview mit eigenem responsivem Dashboard-Layout repariert; Kennzahlen, Warteschlangen und Administratorhinweise bleiben auf Desktop, Tablet und Mobilgeräten klar getrennt.
- Discord-Webhook-Editor um Template-Autofill aus dem versionierten Event-Katalog und eine kompakte, durchsuchbare Mehrfachauswahl für abonnierte Events erweitert.
- Discord-Chat-Webhooks um unabhängige Mehrkanal-Abonnements und ein manuelles Broadcast-Panel erweitert; Broadcast-only-Ziele, Mehrfachauswahl, eigene Zustellhistorie und Retry werden direkt vom Backend unterstützt.
- Discord-Channel-Webhooks als einzige Discord-Integration beibehalten; Staff-Navigation, API und Infrastruktur auf direkte Backend-Zustellung bereinigt.
- Alembic-Schema für den vorgesehenen Clean-Setup in einer aktuellen `0001_baseline` konsolidiert.
- Gateway builds now normalize frontend directory permissions to `0755` and file permissions to `0644`, ensuring bundled assets such as `rbf-fleet-icon.png` remain publicly readable.



## 2026-07-28 - Default discovery results and CSS cascade restoration

- Loads all builds and all published guides immediately when their library pages open.
- Clearing filters now returns to the complete result set instead of hiding the result panel.
- Restores the shared CSS to one deterministic stylesheet to match the pre-refactor cascade and prevent production layout drift.
- Adds repository and frontend regression checks for default discovery loading and CSS delivery order.

## 1.0.0 — Produktionsbaseline

### Fixed

- Echte Build-CRUD-Ereignisse serialisieren nun das öffentliche `BuildRead`-Schema statt eines SQLAlchemy-Objekts; `build.created`, `build.updated` und `build.removed` werden dadurch zuverlässig eingeplant und zugestellt.
- Fleet-/Squad-Scope-Metadaten für Registrierungen, Kalender, Builds, Guides, Forum und Einsteiger-Guide vereinheitlicht, sodass reale Ereignisse dieselben Abonnements erreichen wie vorgesehen.
- Event-spezifische Testzustellungen verwenden realistische Payloads; Repository-Prüfungen erzwingen für jedes Event genau einen Publisher, einen serialisierbaren Test-Payload und gültige Template-Felder.
- Unerwartete Fehler in Webhook-Hintergrundaufgaben werden als fehlgeschlagene Zustellung persistiert, statt Einträge dauerhaft im Status `queued` zu belassen.
- Englische Webhook-Nachrichtenvorlagen um vollständige Ressourcendaten und anklickbare Deep-Links erweitert; Webhook-Envelopes qualifizieren relative Ressourcenpfade nun gegen die öffentliche Website-Origin.
- Gelöschte Builds und Guides verlinken in Benachrichtigungen auf ihre weiterhin erreichbaren Übersichtsseiten.
- Alembic-Head-Erkennung im gebauten API-Image korrigiert: Schema-Prüfungen verwenden nun explizit `/app/alembic.ini` statt eines nicht vorhandenen Pfads im installierten Python-Paket.
- Direkt kopierbare, versionierte Nachrichten-Templates für alle unterstützten Webhook-Events unter `docs/webhook-templates/message-templates/` ergänzt.
- Standardnachrichten für Build-Webhooks auf das tatsächliche Feld `data.build_name` korrigiert.
- Update-Erkennung von Git-Diffs auf einen Laufzeitvergleich zwischen Alembic-Head des neu gebauten API-Images und der tatsächlichen PostgreSQL-Revision umgestellt; fehlgeschlagene Migrationen werden im Folgelauf sicher erneut erkannt.
- Admin-Updateanforderungen werden erst nach Erwerb des exklusiven Locks übernommen; parallele Runner verlieren keine Requests und überschreiben keinen laufenden Status mehr.
- Update-Heartbeat und Recovery für verwaiste `queued`-/`running`-Zustände ergänzt; abgebrochene Host-Läufe blockieren keine neuen Anforderungen dauerhaft.
- `--seed` impliziert jetzt immer `--migrate`; `--no-auto-migrate` bricht bei abweichendem Schema vor dem API-Deployment ab.
- Laufende API- und Gateway-Image-IDs werden als exakter Rollback-Punkt erfasst und gegenüber einem nicht reproduzierbaren Rebuild bevorzugt.
- PostgreSQL-Restore um exklusiven Lock, Pre-Restore-Backup, Wartungsmodus, Verbindungsabbruch, Alembic-Upgrade und Readiness-/Smoke-Prüfung erweitert.
- Backup-Zähler im Doctor-Skript auf die tatsächlichen Unterverzeichnisse korrigiert und Backend-Testmodule mit Prozessgruppen-Timeout abgesichert.

- Alembic-Revisions-ID der Registrierungs-Flottenbewerbung auf PostgreSQL-kompatible 26 Zeichen gekürzt und eine 32-Zeichen-Repository-Invariante ergänzt.
- Repository- und Infrastrukturprüfungen an die modularen Setup-/Update-Runner sowie die `.cfg`-Konfiguration angepasst.
- Frontend-Backend-Contract-Test ergänzt, der API-Pfade und gemeinsam verwendete Fachwerte gegen OpenAPI und Backend-Regeln prüft.
- Veralteten internen Registry-Verweis aus dem Frontend-Lockfile entfernt und Fleet-Fokuswerte zwischen Frontend und Backend synchronisiert.
- DNS-/Transportfehler ausgehender Webhooks liefern nun eine konkrete Diagnose für den tatsächlichen Compose-Service `api`.
- Staff-Systemlogs um Tagesfilter, sortierbare IP-Übersicht und ein heuristisches Threat-Level-Dashboard erweitert.
- Audit-Historie für Builds, Forum-Threads/-Beiträge, Leitfäden und den Starter-Leitfaden ergänzt.
- Ingame-Waffenlayout-Konvention als Heck–Breitseite–Bug vereinheitlicht und dadurch vertauschte Bug-/Heck-Kapazitäten katalogweit korrigiert.
- Lange Build-Notizen werden im Offline-Build-Bild vollständig und mit dynamischer Seitenhöhe ausgegeben.
- Build-Manager um Schiffsvorschau, Crew-Rollenbilder und kategoriespezifische Bildplatzhalter erweitert; Stammdaten-Bilder bleiben hochladbar.
- Schiffsgeschwindigkeiten als getrennte Basis- und Cruise-Maximalwerte modelliert; Prozent- und Flachboni verwenden die verifizierte Ingame-Formel.

- Build-Designer auf bis zu acht Upgrade-Slots erweitert: 4 Standard + 1 Forschungsbelohnung + 2 durch Structural Expansion + 1 schiffsspezifischer Extra-Slot
- Upgrade-Katalog auf 32 aktuelle Ingame-Upgrades aus den Bereichen Geschwindigkeit, Expedition, Schutz, Kampf, Ungewöhnlich und Mörser re-auditiert
- globale Upgrade-Werte als Standard beibehalten; schiffsspezifische Sparse-Overrides bleiben für jeden einzelnen Schiffsstammdatensatz editierbar
- Upgrade-Auswahl im Build-Designer nach den Ingame-Bereichen gruppiert
- erfolgreiche `/api/health`- und `/api/health/ready`-Probes aus System- und NGINX-Zugriffslogs ausgeblendet; fehlgeschlagene Checks bleiben sichtbar
- Systemlog-Ansicht um einen serverseitigen IP-Filter einschließlich gefilterter Kennzahlen erweitert
- schiffsspezifische Upgrade-Effektwerte als wartbare Sparse-Overrides in API, Datenmodell und Stammdatenverwaltung ergänzt
- Build-Designer und serverseitige Build-Berechnung verwenden automatisch die Upgrade-Werte des gewählten Schiffs
- Spezialisten auf genau einen Eintrag je Art vereinheitlicht; Mengen-Counter und stapelbare Effekte entfernt
- Matrosenwert als zu erfüllendes Minimum statt als Obergrenze umgesetzt und Speichersperren transparent aufgelistet
- „Share Build“-Aktion zum Kopieren öffentlicher Build-Links ergänzt
- HTTP-500-Fehler der Staff-API-Logs durch Schema-Reparaturmigration und robuste Summenabfragen behoben
- Build-Designer-Schiffskatalog auf 67 Datensätze aktualisiert, inklusive Event-Schiff Leopard
- Ice Lantern mit +5% Geschwindigkeit, Laderaum und Haltbarkeit ergänzt
- De Zeven Provincien und Sovereign gegen aktuelle Ingame-Panels re-auditiert
- alle 67 Schiffsstammdaten durch Ingame-Screenshots beziehungsweise Event-Tooltips verifiziert
- La Creole, Black Wind, Russia, San Martin und Le Requin final korrigiert
- Vite-Hauptchunk durch Rolldown-Code-Splitting unter die Warnschwelle aufgeteilt
- Schiff-Seeds nach Rate modularisiert und durch gemeinsame Factory/Qualitätsregeln abgesichert
- Stammdatenverwaltung optisch und responsiv zu einem Katalog-Arbeitsbereich überarbeitet
- Upgrade-Slot-Grenze in API, Datenbank und Build-Designer auf maximal acht vereinheitlicht
- stabile FastAPI-/Vue-Modulstruktur und PostgreSQL/Alembic-Produktionspfad
- produktive Seeds von Beispiel-Builds, Guides, Forenbeiträgen, Gruppen, Events und Demo-Dateien befreit
- v1-Datenmigration entfernt bekannte unveränderte 0.x-Mockdaten und bewahrt eigene Inhalte
- Seed-Manager nach System-, Schiff- und Build-Option-Verantwortung aufgeteilt
- kleine Node-Unit-Testbasis für Build-Rechnung, Crew, Präferenzen und Datum ergänzt
- isolierter Backend-Test-Runner und getesteter pre-v1→v1-Datenmigrationspfad
- normalisierte Rollen-, Flotten-, Profil-, Squad- und Build-Designer-Daten
- idempotente, versionierte Stammdaten-Seeds mit geschützten Admin-Overrides
- vollständige Stammdatenverwaltung, Markdown-Inhalte und Bearbeitungsabläufe
- Build-Designer mit verifizierten Segel-, Laternen-, Spezialisten- und Waffenregeln
- Cookie-Consent-Historie und bereinigte öffentliche Assets
- Raspberry-Pi-Einrichtung, TLS, Firewall, systemd, Backups und Diagnosewerkzeug
- konsolidierte v1.0-Dokumentation; historische Zwischenstands-Dokumente entfernt
- getrennte GitHub-CI-Jobs, reproduzierbare Release-Artefakte, Dependabot und optionales CD
- zentrale UTC-Zeitquelle ohne veraltete `datetime.utcnow()`-Verwendung
- große Verantwortungsblöcke aus Build-Statistik, Build-Formular und Systembetrieb extrahiert

Frühere 0.x-Stände waren interne Entwicklungsstände und werden ab v1.0 nicht mehr separat
dokumentiert. Das Produktionsschema ist in `0001_baseline` konsolidiert und für einen frischen Clean-Setup ausgelegt.
Historische Entwicklungsdatenbanken werden nicht per In-Place-Migration übernommen.

- Build-Persistenz als strikt referenzbasiertes 3NF-Modell abgesichert: Endwerte werden nie gespeichert, alte Builds werden bei jedem Lesen aus aktuellen Schiff-/Optionsreferenzen neu berechnet.
- Repository-Invariante und Integrationstest verhindern künftig berechnete Ergebnisfelder beziehungsweise Build-Snapshots in der Datenbank.
## 1.0.0

- New Captain Guide supports linked guides and builds.

## 2026-07-28 — Build Designer option visuals

- Added screenshot-derived icons for all 32 ship upgrades and all 51 specialists.
- Added distinct sail and lantern visuals plus additional-sail consumable icons.
- Replaced the equipment and specialist native selects with an accessible,
  icon-aware picker that shows localized effect values directly in the menu.
- Added seed/asset consistency tests and documented icon provenance.
