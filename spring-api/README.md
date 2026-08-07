# Spring Boot API

Die Spring-Anwendung ist das vollständige Backend des Portals. Sie implementiert alle Operationen aus `contracts/api-contract.json` nativ und besitzt Authentifizierung, Autorisierung, Fachlogik, Persistenz, Flyway, Seed, Audit, Integrationen und Betriebs-APIs.

Die Nutzung, Cookie-/CSRF-Sicherheitsgrenze, Fehlersemantik und der generierte
Endpunktindex sind unter `docs/reference/API.md` dokumentiert.

## Modularchitektur

Der HTTP-Vertrag wird als typisierte Interfaces unter `contract/api/` und als
Transport-DTOs unter `api/dto/` generiert. Jedes Fachmodul implementiert die
zugehörigen Interfaces mit eigenen Controllern und gliedert seinen Code in
`controller`, `filter`, `service`, `mapper`, `dto`, `entity` und `repository`.
Generische `model`-Pakete sind verboten. Modulinterne DTOs kapseln Übergaben zu
Integrationen oder komplexen Fachabläufen; sie ersetzen keine generierten API-DTOs.

Controller implementieren die generierten `*Api`-Interfaces, binden ausschließlich
typisierte Request-/Response-DTOs und delegieren fachliche Arbeit an Services.
Öffentliche Service-Grenzen geben keine Entities, JDBC-Zeilen oder
`Map<String,Object>` weiter. Mapper sind die einzige Stelle für
Entity-/Zeilen-/DTO-Konvertierung. Repositories kapseln Persistenz; SQL-Definitionen
liegen innerhalb der jeweiligen Repository-Schicht unter `repository/queries`.
Services enthalten weder SQL-Literale noch Zugriffe auf den generischen JDBC-Executor.
Es gibt keinen zentralen Dispatcher und keine Operation-Handler.

Der Laufzeitpfad ist damit bewusst eindeutig:

```text
HTTP -> Filter/Security -> Controller -> Service -> Repository -> PostgreSQL
                                  |          |
                                  |          +-> Mapper -> API-/Modul-DTO
                                  +-> HTTP-Status/Header/Cookies
```

Import- und Typkonsistenz werden zusätzlich im Spring-Strukturaudit geprüft;
`mvn verify` bleibt die autoritative Prüfung für vollständige Java-/MapStruct-
Kompilierung und Spring-Integration.

```bash
mvn -f spring-api/pom.xml verify
mvn -f spring-api/pom.xml spring-boot:run
```

Wichtige Regeln:

- Java 21 und Spring Boot 4.1.
- PostgreSQL als Produktionsdatenbank.
- Flyway ist alleiniger Schemabesitzer.
- Hibernate validiert nur; Open Session in View ist aus.
- MapStruct bricht bei nicht zugeordneten Zielfeldern ab.
- Spring Security und CSRF schützen alle privaten Operationen.
- Listenabfragen müssen gebündelt und paginationstauglich sein.
