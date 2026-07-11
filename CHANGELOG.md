# Changelog

## 1.0.0 — Produktionsbaseline

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
