# Entwicklung

## Schnelle Orientierung für Repository-Agenten

`AGENTS.md` ist der verbindliche Arbeitsleitfaden. Agenten beginnen anschließend
mit [`.agents/ONBOARDING.md`](../../.agents/ONBOARDING.md) und einem aktuellen,
geheimnisfreien Snapshot:

```bash
bash .agents/scripts/project-context.sh
```

Der Projekt-Cache beschleunigt die Navigation, ersetzt aber weder diese
Entwicklungsdokumentation noch die betroffenen Quell-, Test- und
Konfigurationsdateien.

## Backend

Voraussetzungen sind Java 21, Maven 3.9+ und PostgreSQL. Für die vollständigen
Integrationstests ist Docker mit Testcontainers erforderlich.

```bash
mvn -f spring-api/pom.xml spring-boot:run
```

Die lokale Konfiguration wird aus den in `application.yml` dokumentierten
Umgebungsvariablen gespeist. PostgreSQL ist die einzige unterstützte Datenbank.
Flyway migriert das Schema; Hibernate prüft es mit `ddl-auto=validate`.

Backend-Änderungen folgen der aktuellen Modulgrenze:

```text
OpenAPI -> generiertes API-DTO -> Controller -> Service -> Repository
                                  |            |
                                  |            +-> PostgreSQL
                                  +-> Mapper <-> DTO/Entity/Row
```

Controller besitzen die Spring-MVC-Routen, bleiben HTTP-orientiert und validieren typisierte DTOs direkt. Services
besitzen Fachlogik, Autorisierung und Transaktionen, aber weder SQL noch rohe
HTTP-/DB-Repräsentationen. Repositories besitzen Persistenz und Query-Kataloge;
Mapper besitzen die Repräsentationswechsel. Fachmodulinterne Übergabeobjekte
liegen in `dto`, Persistenzzustand in `entity`; generische `model`-Pakete sind
nicht zulässig. Neue oder verschobene Java-Typen müssen mit expliziten,
auflösbaren und verwendeten Imports eingecheckt werden.

## Frontend

```bash
cd frontend
cp .env.example .env
npm ci
npx playwright install chromium
npm run dev
```

Node 22 entspricht der CI. Playwright Chromium wird einmalig lokal installiert;
CI installiert Browser und Systemabhängigkeiten vor dem vollständigen Gate. Das
Lockfile muss ausschließlich öffentliche Registry-URLs enthalten.

## Befehle

```bash
make test       # Repository-, Security-, Java-, Frontend- und Infrastrukturchecks im Schnellmodus
make test-full  # vollständige Spring-, PostgreSQL-, Frontend- und Recovery-Prüfung
make validate   # vollständiger Release-Gate
make clean      # generierte Dateien und Buildausgaben entfernen
make clean-all  # zusätzlich lokale Abhängigkeitsumgebungen entfernen
make check-tree # sauberen, paketfreien Repository-Baum prüfen
```

Für fokussiertes Feedback stehen insbesondere folgende Einstiege bereit:

```bash
mvn -f spring-api/pom.xml -Dtest=ApplicationIntegrationTest test
cd frontend && npm run test:browser
```

Für einen vorhandenen Diff kann `bash .agents/scripts/check-changes.sh` die
kleinste passende Prüfmenge anzeigen. Querschnittliche Änderungen bleiben immer
ein Fall für `make validate`.

Neue API-Funktionen benötigen Berechtigungs-, Erfolgs- und Fehlerfälle. Wachsende
Listen brauchen begrenzte Pagination, Such- und Domänenfilter. Collections werden
gebündelt oder über Projektionen geladen; Query-Count-Tests sichern kritische
Assembler gegen N+1-Regressionen ab.

## Abhängigkeiten

Backend-Abhängigkeiten werden ausschließlich in `spring-api/pom.xml` gepflegt.
MapStruct muss bei nicht zugeordneten Zielfeldern fehlschlagen. Frontend-Abhängigkeiten
werden über `frontend/package-lock.json` reproduzierbar installiert.
