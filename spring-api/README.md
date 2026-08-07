# Spring Boot API

Die Spring-Anwendung ist das vollständige Backend des Portals. Sie implementiert alle Operationen aus `openapi/openapi.json` nativ und besitzt Authentifizierung, Autorisierung, Fachlogik, Persistenz, Flyway, Seed, Audit, Integrationen und Betriebs-APIs.

Die Nutzung, Cookie-/CSRF-Sicherheitsgrenze, Fehlersemantik und der generierte
Endpunktindex sind unter `docs/reference/API.md` dokumentiert.

## Modularchitektur

`openapi/openapi.json` ist die externe HTTP-Spezifikation. Daraus werden nur die
Transport-DTOs unter `api/dto/` generiert. Die Spring-MVC-Bindings liegen bewusst
direkt in den Modul-Controllern: `@GetMapping`/`@PostMapping`,
`@PathVariable`, `@RequestParam` sowie `@Valid @RequestBody` sind Controller-
Verantwortung und werden mit `audit_controller_contract.py` gegen OpenAPI geprüft.

Jedes Fachmodul gliedert seinen Code nach Bedarf in `controller`, `filter`,
`service`, `mapper`, `dto`, `entity` und `repository`. Generische `model`- oder
`contract`-Pakete sind verboten. Modulinterne DTOs kapseln typisierte Übergaben
für Fachabläufe; API-DTOs bilden ausschließlich den HTTP-Rand.

Controller sind HTTP-orientiert, validieren typisierte Request-DTOs und delegieren
fachliche Arbeit an Services. Öffentliche Service-Grenzen geben keine Entities,
JDBC-Zeilen oder `Map<String,Object>` weiter. Mapper besitzen
Entity-/Zeilen-/DTO-Konvertierung; generische ObjectMapper-basierte
"Contract-Conversion" ist kein Anwendungs-Layer. Repositories kapseln Persistenz;
SQL-Definitionen liegen innerhalb der jeweiligen Repository-Schicht unter
`repository/queries`. Services enthalten weder SQL-Literale noch Zugriffe auf den
generischen JDBC-Executor.

Der Laufzeitpfad ist damit bewusst eindeutig:

```text
HTTP -> Filter/Security -> Controller -> Service -> Repository -> PostgreSQL
                           |           |
                           |           +-> Mapper <-> API-/Modul-DTO/Entity/Row
                           +-> DTO-Validierung + HTTP-Status/Header/Cookies
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
