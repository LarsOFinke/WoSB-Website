# Spring Boot API

Die Spring-Anwendung ist das vollständige Backend des Portals. Sie implementiert alle Operationen aus `contracts/api-contract.json` nativ und besitzt Authentifizierung, Autorisierung, Fachlogik, Persistenz, Flyway, Seed, Audit, Integrationen und Betriebs-APIs.

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
