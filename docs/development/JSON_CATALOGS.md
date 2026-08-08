# JSON-Quellen und Kataloge

Handgepflegte JSON-Daten folgen denselben KISS-/SOLID-Grenzen wie Quellcode: eine
Datei besitzt eine klar erkennbare Verantwortung, Änderungen sollen kleine Diffs
erzeugen und große Sammeldokumente werden nicht als Autorenformat verwendet.

## OpenAPI

Die kanonische Autorenquelle liegt unter `openapi/source/`:

- `root.json` enthält ausschließlich OpenAPI-Metadaten,
- `schemas/<SchemaName>.json` enthält genau ein Schema,
- `operations/<operationId>.json` enthält genau eine Methode mit Pfad und Operation.

`openapi/openapi.json` ist das deterministisch zusammengesetzte
Kompatibilitätsartefakt für Generatoren, Audits und externe Werkzeuge. Es wird nicht
von Hand editiert.

```bash
python3 infrastructure/scripts/generation/assemble_openapi.py
python3 infrastructure/scripts/generation/generate_api_dtos.py
python3 infrastructure/scripts/generation/generate_api_reference.py
```

`assemble_openapi.py --check` schlägt bei doppelten Operationen, abweichenden
`operationId`-Dateinamen oder einem veralteten zusammengesetzten Vertrag fehl.

## Build-Stat-Katalog

`spring-api/src/main/reference/build-stats/` besitzt genau eine Stat-Definition pro
Datei. Das numerische Präfix konserviert die fachliche Reihenfolge; der stabile Key
im Dateinamen macht die Verantwortung sichtbar. `BuildStatCatalog.java` bleibt ein
generiertes Laufzeitartefakt.

```bash
python3 infrastructure/scripts/generation/generate_build_stat_catalog.py
```

## Seed-Kataloge

Große Build-Option- und Schiffsraten-Dateien sind in einzelne Seed-Einträge geteilt:

- `seed/builds/options/<category>/<NNN-seed-id>.json`,
- `seed/ships/rates/<rate>/<NNN-seed-id>.json`.

Ein Dateipräfix definiert ausschließlich die bisherige stabile Katalogreihenfolge;
die fachliche Identität bleibt `seed_id`. Spring lädt die Einträge direkt und gibt
sie als read-only Maps weiter. `seed/manifest.json` referenziert die Kataloge über
Globs statt über Monolith-Dateien.

## Größen-Gate

Handgepflegte JSON-Dateien unter OpenAPI-Source, Reference-Katalogen, Seeds und
Frontend-Testfixtures dürfen höchstens **420 Zeilen** besitzen. Generierte
Kompatibilitätsdateien wie `openapi/openapi.json` und Lockfiles sind davon bewusst
ausgenommen. Das Gate liegt in `infrastructure/scripts/quality/check_repository.py`.
