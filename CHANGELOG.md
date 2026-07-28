# Changelog

## Unreleased

### Owned-ship seed audit

- Re-audited 28 owned ships from 173 current in-game screenshots and updated their displayed speed ranges plus the corrected Mordaunt, Russia and Sans Pareil statistics.
- Added sparse screenshot-backed upgrade values for 19 rate I–II and V–VI ships while preserving the normalized rate III–IV defaults.
- Corrected the global Teak Frames armor value from `15` to `1.5`.
- Extended the JSON seed schema and bootstrap so ship-specific upgrade values resolve by stable upgrade IDs, survive normal reseeds and are restored by the master-data admin workflow.
- Documented account-level upgrade-slot handling and retained ambiguous mortar layouts until quantified modification panels are available.

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

## 1.0.0

- New Captain Guide supports linked guides and builds.
