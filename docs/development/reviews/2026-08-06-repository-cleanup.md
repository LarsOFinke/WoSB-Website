# Repository-Cleanup vom 6. August 2026

## Ziel

Nach dem Schichten- und DTO-Refactoring wurde das Repository auf verwaiste
Pakete, tote Klassen, leere Quellverzeichnisse, überholte Hilfsabstraktionen und
inkonsistente Modulzuordnungen geprüft. Der Cleanup verändert keine API-Routen
oder fachlichen Verträge, sondern schärft die bestehende Architektur:

```text
Controller -> Service -> Repository
                  |          |
                  v          v
                Mapper <-> DTO / Entity / Datenbankzeile
```

## Bereinigte Strukturen

- Alle generischen Modul-`model`-Pakete wurden entfernt.
- Interne Build- und Security-Übergabeobjekte liegen in fachlich eindeutigen
  Modul-`dto`-Paketen.
- Der generierte Build-Stat-Katalog liegt als serviceeigener Fachkatalog im
  Build-Modul; der Generator schreibt direkt in dieses Zielpaket.
- Der Masterdata-Seed-Katalog liegt in der Repository-Schicht.
- Der Webhook-Ereigniskatalog liegt in der Service-Schicht und verwendet ein
  internes, mapperbasiert übersetztes DTO.
- Das leere `account/model`-Verzeichnis und alle weiteren leeren
  Java-Quellverzeichnisse wurden entfernt.
- Das ungenutzte `SiteRoleRepository` wurde gelöscht.
- Zeitgebundene Refactoring-Berichte wurden unter `docs/development/reviews/`
  zusammengeführt statt als lose Dateien im Repository-Root zu verbleiben.

## Bereinigte Codepfade

- Verbliebene Controller-Aufrufe des bereits entfernten generischen
  `body(body, Type.class)`-Helpers wurden auf die typisierten Request-DTOs
  umgestellt.
- Tote Controller- und Parameter-Helfer wurden entfernt.
- Der obsolete `RequestParameters`-Zwischenschritt wurde gelöscht.
- Controller bauen typisierte Query-Parameter nicht mehr in
  `Map<String, Object>` um. Modulfilter erhalten konkrete Werte wie `String`,
  `Long`, `boolean`, `limit` und `offset`.
- Überflüssige lokale `AuthenticatedUser`-Variablen wurden entfernt, wenn nur die
  Authentifizierungsprüfung benötigt wird; `CurrentUser.require()` bleibt als
  explizite Sicherheitsgrenze bestehen.
- Imports und Tests wurden an die eindeutigen Paketverantwortungen angepasst.
- Das Repository-Cleanup-Skript verwendet für Dateiartefakte keinen
  widersprüchlichen `find -prune`/`-delete`-Pfad mehr; `make clean` beendet den
  Hygiene-Lauf wieder zuverlässig mit Erfolg.

## Neue Regression-Gates

Das Spring-Architekturaudit blockiert nun zusätzlich:

- generische `model`-Pakete in Fachmodulen;
- leere Java-Quellverzeichnisse;
- den entfernten `RequestParameters`-Helper;
- rohe Parameter-Maps und alte Body-Casts in Controllern;
- Modul-Repositories ohne Anwendungskonsumenten.

Die vorhandenen Regeln für typisierte API-Grenzen, Mapper-Verantwortung,
Service-/Repository-Trennung, SQL-Platzierung und vollständige OpenAPI-Abdeckung
bleiben bestehen.

## Validierung

Erfolgreich geprüft wurden:

- 177 OpenAPI-Operationen in 34 generierten API-Interfaces und 26
  Modul-Controllern;
- 179 generierte API-DTOs gegen den aktuellen OpenAPI-Vertrag;
- Spring-Architekturaudit über 465 Produktions-Javaquellen;
- Java-Syntax und internes Package-/Import-Geflecht;
- Dokumentations-, Cache-, Infrastruktur- und Strict-Tree-Gates;
- Recovery-Testpaket mit 8 bestandenen Tests;
- 157 dependency-freie Frontendtests sowie die Build-Designer-Regression.

## Umgebungsgrenzen

Maven war im bereitgestellten Ausführungsumfeld nicht installiert und konnte
wegen fehlendem externem DNS-/Netzwerkzugriff nicht nachinstalliert werden.
Deshalb wurden `mvn verify`, vollständige Spring-Kontextstarts und
PostgreSQL-Testcontainers hier nicht ausgeführt.

Der vollständige Frontend-Gate-Lauf erreicht nach den 157 dependency-freien Tests
und der Build-Designer-Regression den SFC-Schritt, kann dort ohne installiertes
`node_modules` beziehungsweise `@vue/compiler-sfc` jedoch nicht fortgesetzt
werden. Generierte und ignorierte Frontend-Locale-Dateien sowie alle Python- und
Pytest-Caches wurden vor der Auslieferung entfernt.
