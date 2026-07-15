# Konfiguration

## Quellen und Priorität

Die Anwendung trennt bewusst zwei Arten von Konfiguration:

1. `config/*.cfg` enthält nicht geheime, versionskontrollierte Einstellungen.
2. `.env` enthält umgebungsabhängige Werte und Geheimnisse.
3. Prozessvariablen überschreiben gleichnamige Werte aus `.env`.

Standardmäßig werden alle `.cfg`-Dateien im Verzeichnis `backend/config` alphabetisch
gelesen. `RBF_CONFIG_DIR` kann ein anderes Verzeichnis auswählen. Für kleine Deployments
kann `RBF_CONFIG_FILE` auf genau eine `.cfg`-Datei zeigen. TOML wird nicht mehr geladen.

## Dateien

- `application.cfg`: Name, Version und API-Präfix
- `logging.cfg`: Log-Level, Format und Ausgabekanäle
- `session.cfg`: Cookie-Name, SameSite und Lebensdauer
- `uploads.cfg`: Größenlimits je Dateityp

Neue fachliche Einstellungen gehören in eine eigene Section und erhalten einen eigenen
Reader unter `src/app/configuration/readers`. Direkte `ConfigParser`-Zugriffe außerhalb
des Konfigurationspakets sind zu vermeiden.

## Laufzeitwerte

Die Beispiele `.env.example` und `.env.production.example` dokumentieren die notwendigen
Werte. Insbesondere gehören Datenbank-Zugangsdaten, Seed-Passwörter, CORS-Ursprünge und
Dateisystempfade nicht in `.cfg`-Dateien.

Produktionsregeln werden beim Laden validiert: PostgreSQL ist verpflichtend,
`DB_SCHEMA_MODE=migrate` übergibt das Schema an Alembic und Session-Cookies müssen sicher
sein.
