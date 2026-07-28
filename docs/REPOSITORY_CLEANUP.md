# Repository-Aufräumregeln

## Verantwortlichkeiten

- Route-Module koordinieren HTTP, Berechtigungen und Fehlerabbildung; Fachlogik bleibt in Services.
- Services werden nach Use Case getrennt. Ein Modul soll nicht zugleich CRUD, Validierung und externe Transporte besitzen.
- Frontend-Module referenzieren Assets als Dateien; Binärdaten und Base64-Payloads gehören nicht in JavaScript.
- Die globale CSS-Cascade liegt in numerisch geordneten Schichten unter `frontend/src/styles/global/`. Fachoberflächen besitzen Styles im jeweiligen Modul; CSS-`@import`, neue Root-Blöcke und globale Altselektoren sind verboten.
- Das SQLAlchemy-Modell ist die fachliche Schemaquelle. `0001_baseline` ist der eingefrorene Startpunkt für neue Datenbanken.

## Größenbudgets

`python scripts/check_repository.py` verhindert neue Monolithen:

- Service-Module: maximal 525 Zeilen
- Route-Module: maximal 300 Zeilen
- Frontend-Seiten: maximal 1.050 Zeilen; Route-Pages bleiben reine Komposition
- JavaScript-Module: maximal 250 KB und keine eingebetteten Bilddaten
- Globale CSS-Schicht: maximal 75 KB und 3.500 Zeilen; gesamte Frontend-CSS-Quelle maximal 400 KB

Budgets sind Schutzplanken, keine Zielwerte. Neue Funktionen sollen möglichst deutlich darunter bleiben.

## Lokale Artefakte

```bash
make clear-pycache
```

Der Befehl entfernt `__pycache__`, Bytecode sowie Pytest-, Ruff- und Mypy-Caches im Backend.
`node_modules`, Buildausgaben, virtuelle Umgebungen und `*.egg-info` dürfen nicht eingecheckt werden.

## Schemaänderungen

1. Modelle ändern.
2. Eine kleine Alembic-Revision erzeugen.
3. Revision fachlich prüfen; keine generierten Datenmigrationen ohne explizite Absicherung.
4. `make test-full` ausführen.
5. Upgrade und Downgrade dokumentieren.


## KISS und SOLID im Projekt

- Eine Route übersetzt HTTP in einen Use Case; sie implementiert den Use Case nicht selbst.
- Ein Service besitzt eine fachliche Änderungsursache. Transporte, Retention und Darstellung bleiben getrennt.
- API-Schemas geben nur die Daten frei, die der konkrete Consumer benötigt. Eingebettete Identitäten nutzen `UserReferenceRead`.
- Route-Pages orchestrieren Page-Composables und Präsentationskomponenten; wiederkehrende UI-Rahmen werden als kleine Slot-Komponenten geteilt.
- Abstraktionen entstehen erst bei echter Wiederholung. Ein klarer lokaler Ausdruck ist besser als ein generischer Framework-Baustein.
- Sicherheits- und Datenschutzgrenzen werden durch Tests und Repository-Gates erzwungen, nicht nur dokumentiert.
