# Repository-Aufräumregeln

## Verantwortlichkeiten

- Route-Module koordinieren HTTP, Berechtigungen und Fehlerabbildung; Fachlogik bleibt in Services.
- Services werden nach Use Case getrennt. Ein Modul soll nicht zugleich CRUD, Validierung und externe Transporte besitzen.
- Frontend-Module referenzieren Assets als Dateien; Binärdaten und Base64-Payloads gehören nicht in JavaScript.
- Das SQLAlchemy-Modell ist die fachliche Schemaquelle. `0001_baseline` ist der eingefrorene Startpunkt für neue Datenbanken.

## Größenbudgets

`python scripts/check_repository.py` verhindert neue Monolithen:

- Service-Module: maximal 525 Zeilen
- Route-Module: maximal 300 Zeilen
- Frontend-Seiten: maximal 1.050 Zeilen
- JavaScript-Module: maximal 250 KB und keine eingebetteten Bilddaten

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
