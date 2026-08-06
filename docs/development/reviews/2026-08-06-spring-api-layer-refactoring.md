# Spring-API-Refactoring

## Ziel

Die Spring-API wurde von einer zentral dispatchenden, handlerbasierten Struktur auf
klassische, fachmodular getrennte Spring-Schichten umgestellt:

```text
OpenAPI-Vertrag
  -> generiertes API-Interface + API-DTO
  -> Modul-Controller
  -> Modul-Service
  -> Modul-Repository
  -> Modul-Mapper
  -> API-/Modul-DTO oder Entity / PostgreSQL
```

Die Pakete `controller`, `filter`, `service`, `mapper`, `dto`, `entity` und
`repository` liegen innerhalb der jeweiligen Fachdomäne. Mehrdeutige generische
`model`-Pakete sind nicht Teil des Zielbilds: Transportdaten gehören nach `dto`,
Persistenzobjekte nach `entity` und Kataloge in die verantwortliche Service- oder
Repository-Schicht. Ein Layer wird nur angelegt, wenn das Modul dafür eine reale
Verantwortung besitzt; leere Platzhalter oder künstliche Abstraktionen werden nicht
erzeugt.

## Bereinigter Ausgangszustand

Vor dem Refactoring waren HTTP-Routen über einen zentralen Dispatcher und
modulbezogene Operation-Handler verdrahtet. Fachmodule waren teilweise flach
organisiert, Services griffen auf einen generischen JDBC-Dienst zu, und SQL war in
43 Serviceklassen verteilt. Dadurch waren Transport, Fachlogik und Persistenz nur
unzureichend getrennt.

## Umgesetzte Änderungen

- 177 OpenAPI-Operationen werden durch 34 generierte, typisierte API-Interfaces
  beschrieben und eindeutig von 26 Modul-Controllern implementiert.
- 179 generierte Request-/Response-DTOs bilden den HTTP-Vertrag ab; benannte
  Modul-DTOs kapseln interne Persistenz- und Integrationsübergaben.
- Controller und öffentliche Service-Grenzen transportieren weder Entities noch
  JDBC-Zeilen oder Roh-Maps. Nur Mapper erzeugen API-Repräsentationen.
- Zentraler API-Dispatcher, Operation-Handler-Basisklassen, 26 konkrete
  Operation-Handler und die alten generierten Controller wurden entfernt.
- Controller enthalten ausschließlich HTTP-Bindung und delegieren an Services.
- Fachlogik, Autorisierung und Transaktionsgrenzen liegen in Modul-Services.
- Generischer JDBC-Zugriff ist nur noch aus Persistenz- und Repository-Klassen
  erreichbar.
- SQL-Definitionen wurden aus 43 Services in fachmodulbezogene Query-Kataloge
  unter `repository/queries` verschoben. Services enthalten keine SQL-Literale.
- Mapper, DTOs, Entities, Filter und Repositories wurden den jeweiligen
  Fachmodulen und eindeutigen Layer-Paketen zugeordnet.
- Auch die Core-Health-/Readiness-Pfade folgen Controller -> Service -> Repository.
- Architektur- und Generierungsgates wurden auf das neue Schichtenmodell
  umgestellt und verhindern Rückfälle in Dispatcher-, Handler- oder
  Service-zu-JDBC-Strukturen.
- Betroffene Tests und Dokumentation wurden auf die neuen Pakete und
  Repository-Abhängigkeiten angepasst.

## Erzwungene Architekturregeln

`infrastructure/scripts/quality/audit_spring_backend.py` prüft unter anderem:

- vollständige und eindeutige Implementierung aller Vertragsoperationen;
- keine zentralen Dispatcher oder Operation-Handler;
- keine Route-Mappings außerhalb der generierten API-Interfaces;
- keine Controller-Zugriffe auf Repository, Entity, JDBC, Flyway oder SQL;
- keine Service-Zugriffe auf generischen JDBC und keine SQL-Literale in Services;
- keine Repository-Abhängigkeiten auf obere Schichten;
- explizite Layer-Pakete für ausführbare Fachmodulklassen;
- bestehende Batch-, Security- und Größeninvarianten.

## Lokale Validierung

Erfolgreich ausgeführt wurden:

- Vertragsgenerierung: 34 Interfaces und 177 Operationen konsistent;
- Spring-Architekturaudit: 26 Controller und 466 Produktions-Javaquellen konsistent;
- internes Package-/Import-Konsistenz-Gate;
- Security-Audit;
- Agent-/Modul-Cache-Gate;
- strukturelle Java-21-Kompilierung des ursprünglichen Layer-Refactorings gegen isolierte
  Spring-/JPA-Schnittstellenstubs;
- strukturelle Kompilierung aller 21 Testquellen gegen dieselben Stubs.

## Umgebungsgrenze

Im bereitgestellten Ausführungsumfeld war Maven nicht installiert und externer
Netzwerk-/DNS-Zugriff stand nicht zur Verfügung. Deshalb konnten
`mvn -f spring-api/pom.xml verify`, echte Spring-Kontextstarts und
PostgreSQL-Testcontainers hier nicht ausgeführt werden. Die Stub-Kompilierung
prüft Java-Typen, Signaturen, Pakete und interne Abhängigkeiten, ersetzt aber keinen
abschließenden Maven-/Runtime-Test in der regulären CI- oder Entwicklungsumgebung.
## DTO-Transition

Das anschließende DTO-Refactoring ist vollständig im
[DTO-Refactoring-Bericht](2026-08-06-spring-api-dto-refactoring.md) dokumentiert. Die aktuelle Zielarchitektur erzwingt typisierte HTTP-DTOs,
modulbezogene Übergabe-DTOs und Mapper als einzige Repräsentationsgrenze.


## Nachgelagerter Repository-Cleanup

Der anschließende Strukturputz entfernte die verbliebenen generischen `model`-Pakete.
Interne Build- und Security-Übergabeobjekte liegen nun in Modul-`dto`-Paketen,
Seed- und Eventkataloge in der verantwortlichen Repository-/Service-Schicht. Zudem
wurden ein ungenutztes Spring-Data-Repository, tote Controller-Helper und der
Map-basierte `RequestParameters`-Zwischenschritt entfernt. Das Architektur-Gate
verhindert leere Quellverzeichnisse, generische `model`-Pakete, rohe Parameter-Maps
in Controllern und Repository-Typen ohne Anwendungskonsumenten.
