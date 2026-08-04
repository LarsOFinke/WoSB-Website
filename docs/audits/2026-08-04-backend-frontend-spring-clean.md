# Backend-/Frontend-Frühjahrsputz

## Geprüfter Umfang

- 358 Java-Quelldateien und 11 Backend-Tests
- 373 Frontend-Quelldateien
- Maven-Abhängigkeiten und Frontend-Abhängigkeiten
- Import-/Referenzsuche für Backend-Klassen und Frontend-Module
- generierte Locale-Dateien, Build-Ausgaben und lokale Artefakte

## Ergebnis

Es wurden keine Dateien gelöscht. Die Kandidaten mit wenigen direkten
Textreferenzen waren entweder:

- dynamisch geladene Frontend-Seiten oder Route-Module,
- deklarative Locale-Kataloge,
- generierte Locale-Ausgaben,
- interne Backend-Komponenten, die über Spring-Komponentenscans bzw. reflektive
  Transport-Registrierung verwendet werden, oder
- bewusst manuelle Recovery-/Administrationswerkzeuge.

Die großen Locale-Kataloge sind deklarative Daten und keine Sammelklassen. Die
größeren Frontend-Seiten `DatabaseBackupsPage.vue` und `BuildCreatePage.vue`
bleiben als gezielte nächste Refactoring-Kandidaten dokumentiert; eine Aufteilung
ohne fachliche Änderung wäre in diesem Durchlauf nicht risikoadäquat.

## Qualitätsprüfungen

- `python3 scripts/audit_spring_backend.py` erfolgreich
- `mvn -Dmaven.repo.local=/tmp/rbf-secure-api-m2 -q test` erfolgreich
- `npm test --prefix frontend` erfolgreich (153 Unit-/Strukturtests plus
  Build-Designer-, Page-Binding-, Locale- und Responsive-Prüfungen)
- `npm ls --prefix frontend --depth=0` ohne extraneous packages
- generierte Locale-Dateien und `frontend/dist` bleiben ignorierte Artefakte

## Bereinigungsentscheidung

Keine spekulativen Löschungen: Die aktuelle Struktur ist durch CI, systemd,
Spring-Scanning und dynamische Frontend-Routen stärker gekoppelt, als eine reine
Dateinamen-/Textsuche erkennen kann. Ein weiteres Refactoring sollte je Modul
mit eigenem Test und separatem Commit erfolgen.
