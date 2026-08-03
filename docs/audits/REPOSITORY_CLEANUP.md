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

## Sicherheitsgate

```bash
make security-audit
```

Der Offline-Audit prüft unter anderem Workflow-Pins, gefährliche GitHub-Trigger, Secret-Muster,
Containerprivilegien, Edge-Header, dynamische Python-Ausführung und die Verschlüsselungsgrenze der
Discord-Webhooks. Bekannte Schwachstellen in Drittanbieterpaketen werden zusätzlich durch den
separaten OSV-Workflow geprüft.

## Lokale Artefakte

```bash
make clean       # Buildausgaben, generierte Locale-Module und Caches entfernen
make clean-all   # zusätzlich lokale Abhängigkeits- und Build-Umgebungen entfernen
make check-tree  # denselben strengen Repository-Baum wie in CI prüfen
```

Buildausgaben, virtuelle Umgebungen, Paketdateien, Prüfsummen, lokale Datenbanken,
Laufzeit-`.env`-Dateien und private Schlüssel dürfen nicht eingecheckt werden. Das gilt insbesondere
für `tools/*/recovery-tool/{build,dist,.venv-build}` und die von Vite erzeugten Locale-Module unter
`frontend/src/locales/generated`. Die Root-`.gitignore`, die bereichsspezifischen Ignore-Dateien und
`scripts/check_repository.py --strict-tree` bilden dafür bewusst drei unabhängige Schutzschichten.
In einem Git-Checkout prüft das Gate die tatsächlich versionierten Dateien und toleriert ignorierte
lokale Abhängigkeiten; in einem exportierten Quellbaum ohne `.git` prüft es dagegen jede enthaltene
Datei.

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
