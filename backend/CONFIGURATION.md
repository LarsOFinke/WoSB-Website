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

Im Container enthält das Image eine leere `config/container.env`. Compose setzt
`RBF_ENV_FILE=/app/config/container.env` und injiziert die tatsächlichen Werte aus
`infrastructure/.env` als Prozessvariablen. Da Prozessvariablen Vorrang haben, erfüllt die
Markerdatei den verpflichtenden Datei-Vertrag, ohne Geheimnisse in das Image zu schreiben.

Produktionsregeln werden beim Laden validiert: PostgreSQL ist verpflichtend,
`DB_SCHEMA_MODE=migrate` übergibt das Schema an Alembic und Session-Cookies müssen sicher
sein.

## Impressum / Anbieterkennzeichnung

Die optionalen `LEGAL_NOTICE_*`-Variablen liefern die initialen Angaben für die öffentliche
Impressumsseite. `LEGAL_NOTICE_PUBLISHED=false` hält die Seite im Entwurfsmodus und gibt keine
personenbezogenen Entwurfsangaben über die öffentliche API aus. Bei
`LEGAL_NOTICE_PUBLISHED=true` sind mindestens Anbietername, vollständige ladungsfähige Anschrift,
Land und E-Mail-Adresse erforderlich; unvollständige Konfigurationen werden beim Start abgewiesen.

Beim ersten Start nach Migration `0013` wird ein Singleton-Datensatz aus der geladenen Umgebung
erzeugt. Solange dieser Datensatz nicht im Staff-Panel angepasst wurde, können aktualisierte
Umgebungswerte ihn beim Anwendungsstart auffrischen. Nach einer Admin-Änderung bleibt die
Datenbankfassung maßgeblich und wird durch Updates nicht überschrieben. Die Aktion
„Auf Umgebungswerte zurücksetzen“ übernimmt bewusst die beim letzten Prozessstart geladenen Werte;
nach Änderungen an `.env` ist daher zuerst ein Neustart erforderlich.

Die Konfiguration bildet keine Rechtsberatung ab. Ob und welche Angaben veröffentlicht werden
müssen, ist für den konkreten Betreiber und das konkrete Angebot rechtlich zu prüfen.
