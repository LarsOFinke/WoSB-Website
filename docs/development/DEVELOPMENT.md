# Entwicklung

## Backend

Voraussetzungen sind Java 21, Maven 3.9+ und PostgreSQL. Für die vollständigen
Integrationstests wird Docker mit Testcontainers empfohlen.

```bash
mvn -f spring-api/pom.xml spring-boot:run
```

Die lokale Konfiguration wird aus den in `application.yml` dokumentierten
Umgebungsvariablen gespeist. PostgreSQL ist die einzige unterstützte Datenbank.
Flyway migriert das Schema; Hibernate prüft es mit `ddl-auto=validate`.

## Frontend

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Node 22 entspricht der CI. Das Lockfile muss ausschließlich öffentliche
Registry-URLs enthalten.

## Befehle

```bash
make test       # Repository-, Security-, Java-, Frontend- und Infrastrukturchecks im Schnellmodus
make test-full  # vollständige Spring-, PostgreSQL-, Frontend- und Recovery-Prüfung
make validate   # vollständiger Release-Gate
make clean      # generierte Dateien und Buildausgaben entfernen
make clean-all  # zusätzlich lokale Abhängigkeitsumgebungen entfernen
make check-tree # sauberen, paketfreien Repository-Baum prüfen
```

Neue API-Funktionen benötigen Berechtigungs-, Erfolgs- und Fehlerfälle. Wachsende
Listen brauchen begrenzte Pagination, Such- und Domänenfilter. Collections werden
gebündelt oder über Projektionen geladen; Query-Count-Tests sichern kritische
Assembler gegen N+1-Regressionen ab.

## Abhängigkeiten

Backend-Abhängigkeiten werden ausschließlich in `spring-api/pom.xml` gepflegt.
MapStruct muss bei nicht zugeordneten Zielfeldern fehlschlagen. Frontend-Abhängigkeiten
werden über `frontend/package-lock.json` reproduzierbar installiert.
