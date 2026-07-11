# Architektur

## Laufzeit

```text
Browser → NGINX Gateway → FastAPI → SQLAlchemy → PostgreSQL
                         ↘ Upload-Verzeichnis
Uptime Kuma → internes Gateway/Health-Endpunkte
```

NGINX liefert das Vue-Frontend und leitet `/api` an FastAPI weiter. PostgreSQL bleibt im internen
Compose-Netz; der Loopback-Port dient nur der Host-Wartung.

## Backend

Fachmodule unter `backend/src/app/modules/<domain>` besitzen nach Bedarf `models`, `schemas`,
`routes` und `services`. Routes übersetzen HTTP, Services enthalten Anwendungslogik, Models bilden
Persistenz ab. Querschnittsthemen liegen in `core` und `db`.

Der Build-Designer trennt deklarative Stat-Metadaten von deterministischer Berechnung. Die
Seed-Orchestrierung ist klein; System-, Schiff- und Build-Option-Katalog werden in getrennten
Modulen synchronisiert. Produktions-Seeds enthalten keine Nutzerinhalte.

## Frontend

`frontend/src/modules/<domain>` kapselt API, Seiten und Komponenten. `core` enthält Shell und
Navigation, `shared` wiederverwendbare Technik. Build-Berechnung, Crew-Zuordnung,
Inventar-Reconciliation, Formular-Defaults, Präferenztransfer und Datumskonvertierung sind reine,
separat testbare JavaScript-Module.

## KISS/SOLID-Leitplanken

- eine fachliche Wahrheit pro Regel; Frontend zeigt, Backend validiert
- keine Abstraktion ohne realen zweiten Anwendungsfall
- UI/Route hängt von Service/Composable ab, nie umgekehrt
- Katalogdaten, Berechnung, Persistenz und Rendering bleiben getrennt
- Soft-Delete für historisch referenzierte Stammdaten
- große Dateien werden nach Verantwortung geteilt; Datenkataloge und Übersetzungen zählen nicht als
  Anwendungslogik
- Repository-Checks begrenzen Wachstum von Python-Services und Vue-Seiten

## Runtime-Grenzen

Laufzeitdaten gehören ausschließlich nach `infrastructure/data`. `.env`, Zugangsdaten, Uploads,
Backups, Caches, Abhängigkeiten und Build-Ausgaben sind nie Teil eines Release-Archivs.
