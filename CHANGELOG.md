# Changelog

## 1.0.0 — Produktionsbaseline

### Fixed

- Converted screenshot-derived ship speed values from raw metres per second to knots before seeding, keeping base ship speed consistent with knot-based sail and upgrade bonuses.

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
