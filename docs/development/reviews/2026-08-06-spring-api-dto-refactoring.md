# Spring-API DTO-Refactoring

## Zielbild

Die Spring-API besitzt jetzt eine explizite und durch Gates erzwungene
Übersetzungsgrenze zwischen HTTP-Vertrag, Fachlogik und Persistenz:

```text
OpenAPI-Vertrag
  -> generiertes API-Interface
  -> generiertes Request-/Response-DTO
  -> Modul-Controller
  -> Modul-Service
  -> Modul-Repository
  -> Modul-Mapper
  -> API-DTO / Modul-DTO / Entity / Datenbankzeile
```

Controller und öffentliche Service-Methoden transportieren keine Entities,
JDBC-Zeilen oder frei weitergereichten `Map<String, Object>`-Strukturen. Mapper
sind die einzige Schicht, die API-Repräsentationen erzeugt oder zwischen
Repository-/Entity-Daten und DTOs übersetzt.

## Umgesetzte Änderungen

- Der OpenAPI-Vertrag erzeugt **179 immutable Java-Records** unter
  `eu.royalblackwater.api.dto`.
- Alle **34 generierten API-Interfaces** besitzen konkrete
  `ResponseEntity<T>`-, `ResponseEntity<List<T>>`-, `ResponseEntity<Resource>`-
  oder `ResponseEntity<Void>`-Signaturen; Wildcards wurden entfernt.
- Alle **177 API-Operationen** sind weiterhin eindeutig über **26 Controller**
  verdrahtet.
- Die 20 HTTP-Fachmodule besitzen jeweils eine Mapper-Schicht.
- Request-Bodies bleiben vom generierten Interface bis zum Service typisiert;
  Controller degradieren DTOs nicht mehr zu `Object` und casten sie nicht erneut.
- Controller erzeugen keine API-Repräsentationen mehr selbst.
- Services instanziieren keine generierten API-DTOs mehr selbst; sie delegieren
  Repräsentationsbildung an Modul-Mapper.
- Öffentliche Service-Signaturen geben weder Entities noch Datenbank-/JSON-Zeilen
  als Roh-Maps weiter.
- Binärdownloads werden über `BinaryDownloadDto` statt untypisierter Responses
  transportiert.
- Persistierte Dateimetadaten, Fleet-Zielmitgliedschaften und Raid-Helper-
  Integrationsdaten besitzen benannte Modul-DTOs.
- Die bewusst dynamische Raid-Helper-JSON-Nutzlast ist in
  `RaidHelperJsonPayloadDto` gekapselt; freie JSON-Strukturen werden nicht mit
  Datenbankzeilen gleichgesetzt.
- Masterdata-Zeilen, Backup-/Update-Control-Dateien, Security-Aggregate,
  Build-Statistiken, Legal-Environment-Fallbacks sowie Webhook-, Privacy-, Fleet-
  und Account-Repräsentationen werden über fachmodulbezogene Mapper aufgebaut.

## DTO-Kategorien

### Generierte API-DTOs

`spring-api/src/main/java/eu/royalblackwater/api/dto/`

Diese Records bilden ausschließlich den versionierten HTTP-Vertrag ab und werden
mit `generate_java_contracts.py` aus `contracts/api-contract.json` erzeugt. Sie
werden nicht manuell editiert.

### Modulinterne DTOs

Benannte Übergabeobjekte liegen im jeweiligen `<domain>/dto`-Paket. Aktuell sind
unter anderem vorhanden:

- `files/dto/StoredFileDto`
- `fleet/dto/FleetMembershipTargetDto`
- `raidhelper/dto/RaidHelperConnectionDto`
- `raidhelper/dto/RaidHelperDestinationConfigDto`
- `raidhelper/dto/RaidHelperTemplateConfigDto`
- `raidhelper/dto/RaidHelperEventDto`
- `raidhelper/dto/RaidHelperDeliveryDto`
- `raidhelper/dto/RaidHelperJsonPayloadDto`
- `shared/dto/BinaryDownloadDto`

Diese DTOs kapseln fachliche oder integrationsbezogene Übergaben, die nicht Teil
des öffentlichen HTTP-Vertrags sind.

## Erzwungene Architekturregeln

`audit_spring_backend.py` und `check_repository.py` verhindern künftig:

- `ResponseEntity<?>` in generierten Interfaces oder Controllern;
- Entity-, Repository-, JDBC- oder SQL-Zugriffe aus Controllern;
- das Zurückstufen typisierter Request-DTOs auf `Object`;
- API-DTO-Konstruktion in Controllern oder Services;
- Entities oder Roh-Maps an öffentlichen Service-Grenzen;
- DTO-Abhängigkeiten auf Controller, Service, Repository oder Entity;
- HTTP-Module ohne Mapper-Schicht;
- veraltete, fehlende oder falsch platzierte generierte API-DTOs;
- Legacy-Transportmodelle im früheren Contract-Paket.

Der DTO-Generator besitzt nun einen fail-closed `--check`-Modus. Das
Repository-Gate vergleicht alle generierten Quellen bytegenau mit dem aktuellen
OpenAPI-Vertrag.

## Validierung

Erfolgreich ausgeführt wurden:

- Spring-Architekturaudit: 177 Operationen, 34 API-Interfaces, 26 Controller und
  466 Produktions-Javaquellen;
- DTO-Generatorprüfung: 179 aktuelle API-DTOs;
- Java-21-Syntaxprüfung: 487 Produktions- und Testquellen;
- Repository-, Dokumentations-, Security-, CSS- und Strict-Tree-Gates;
- Infrastruktur- und Update-/Artifact-Tests;
- Recovery-Tests: 8 bestanden;
- dependency-freie Frontendtests: 157 bestanden.

## Umgebungsgrenze

Maven 3.9 ist im bereitgestellten Ausführungsumfeld nicht installiert und ein
externer Dependency-Download steht nicht zur Verfügung. Deshalb konnten
`mvn -f spring-api/pom.xml verify`, ein echter Spring-Kontextstart und
PostgreSQL-Testcontainers hier nicht erneut ausgeführt werden. Die vorhandenen
Java-Syntax-, Architektur-, Generator-, Repository- und Integration-Gates sind
grün; der reguläre Maven-/Runtime-Lauf bleibt Aufgabe der CI beziehungsweise
einer Entwicklungsumgebung mit Maven-Toolchain.


## Nachgelagerter Repository-Cleanup

Der anschließende Strukturputz entfernte die verbliebenen generischen `model`-Pakete.
Interne Build- und Security-Übergabeobjekte liegen nun in Modul-`dto`-Paketen,
Seed- und Eventkataloge in der verantwortlichen Repository-/Service-Schicht. Zudem
wurden ein ungenutztes Spring-Data-Repository, tote Controller-Helper und der
Map-basierte `RequestParameters`-Zwischenschritt entfernt. Das Architektur-Gate
verhindert leere Quellverzeichnisse, generische `model`-Pakete, rohe Parameter-Maps
in Controllern und Repository-Typen ohne Anwendungskonsumenten.
