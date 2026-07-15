# Changelog

## 1.0.0 — Produktionsbaseline

### Fixed

- Discord-Bot und Discord-Webhooks im Staff-Panel in eigenständige Admin-Seiten und Navigationseinträge getrennt; Bot-Laufzeit und Event-Zustellung funktionieren sichtbar unabhängig voneinander.
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
- API-Container um einen dedizierten ausgehenden Netzwerkpfad für signierte Webhooks und Discord-Bot-Zustellungen ergänzt; Datenbanknetz bleibt intern isoliert.
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
dokumentiert. Datenbankmigrationen bleiben vollständig erhalten, damit bestehende Installationen
verlustfrei auf v1.0 aktualisiert werden können.

## 1.0.0

- New Captain Guide supports linked guides and builds.
