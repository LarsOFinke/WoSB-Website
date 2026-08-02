# Arbeitsleitfaden für Repository-Agenten

Diese Datei gilt für das gesamte Repository. Spezifischere Regeln in einem tiefer
liegenden `AGENTS.md` haben für ihren Teilbaum Vorrang. Verbindliche technische
Details stehen in [docs/QUALITY_STANDARDS.md](docs/QUALITY_STANDARDS.md) und den
dort verlinkten Architekturdokumenten.

## Arbeitsweise

1. Vor Änderungen den betroffenen Ablauf, seine Aufrufer, Tests, Konfiguration und
   Dokumentation lesen. Bei querschnittlichen Aufgaben zuerst einen kurzen Plan
   erstellen.
2. Vorhandene, nicht zum Auftrag gehörende Änderungen erhalten. Keine fremden
   Änderungen zurücksetzen, überschreiben oder ungefragt committen.
3. Die kleinste fachlich vollständige Lösung umsetzen. Bestehende Abstraktionen
   wiederverwenden und neue nur einführen, wenn sie Verantwortung, Lebenszyklus
   oder Austauschbarkeit tatsächlich klären.
4. Fehlerursachen beheben statt Symptome zu kaschieren. Sicherheits-, Datenschutz-,
   Migrations- und Betriebsfolgen immer mitprüfen.
5. Erst gezielt testen, danach die passenden Repository-Gates ausführen. Geändertes
   Verhalten und neue Betriebsabläufe im selben Arbeitsschritt dokumentieren.

## Architektur und Quellcode

- Backend-Domänen bleiben unter `backend/src/app/modules/<domain>/` in Routen,
  Schemas, Services und Modelle getrennt. Routen orchestrieren HTTP; Fachlogik und
  Datenzugriff gehören in Services.
- Abhängigkeiten werden am Rand zusammengesetzt und per Konstruktor oder FastAPI-
  Dependency übergeben, wenn Zustandsverwaltung, Austauschbarkeit oder Tests davon
  profitieren. Reine, kleine Funktionen benötigen keinen DI-Container.
- Frontend-Seiten orchestrieren. Wiederverwendbare Darstellung gehört in
  Komponenten, Zustand und Abläufe in Composables, Netzwerkzugriff in API-Module.
- Infrastruktur-Skripte orchestrieren robuste, idempotente Helper. Kritische
  Dateiänderungen erfolgen möglichst atomar; Fehler müssen einen eindeutigen
  Exit-Code und eine handlungsorientierte Meldung liefern.
- Eine Datei hat eine klar benennbare Hauptverantwortung, die aus ihrem Namen
  hervorgeht. Ab etwa 300–400 Zeilen ist eine Aufteilung in Orchestrator, Service,
  Helper, Transport oder Datenkatalog zu prüfen. Die automatisierte Obergrenze für
  ausführbare Verantwortlichkeiten beträgt grundsätzlich 420 Zeilen; begründete,
  kohäsive deklarative Kataloge sind keine Einladung zu weiteren Sammeldateien.
- KISS vor vorsorglicher Generalisierung; SOLID sinngemäß anwenden. Keine Wrapper,
  Manager oder Basisklassen ohne mindestens einen konkreten Wartbarkeitsgewinn.
- Datenbankschema nur mit Alembic-Migration ändern. Modell, Migration, Upgrade- und
  gegebenenfalls Downgrade-/Recovery-Pfad gemeinsam prüfen.

## Frontend, Sicherheit und Datenschutz

- Für CSS, Responsive-Verhalten, Barrierefreiheit und Design-Tokens gilt
  [docs/CSS_ARCHITECTURE.md](docs/CSS_ARCHITECTURE.md).
- Berechtigungen werden serverseitig erzwungen. Frontend-Guards sind nur UX.
- Keine Secrets, Tokens, personenbezogenen Inhalte oder vollständigen IP-Adressen
  in Quellcode, Fixtures, Logs, Webhooks oder Fehlermeldungen aufnehmen.
- Neue personenbezogene Daten brauchen Zweck, Rechts-/Betriebsgrundlage,
  Aufbewahrung sowie Export-, Berichtigungs- und Löschpfad.
- Webhooks sind sparsame Audit- und Aktionshinweise, kein Überwachungsinstrument.
  Zustellung darf den primären Geschäftsablauf nicht unkontrolliert blockieren.

## Prüfungen und Abschluss

Gezielte Tests während der Entwicklung ausführen. Vor Abschluss einer
querschnittlichen Änderung gilt, soweit lokal verfügbar:

```bash
make validate
```

Mindestens müssen die direkt betroffenen Linter und Tests sowie
`python scripts/check_repository.py --strict-tree` erfolgreich sein. Generierte
Artefakte (`dist`, Caches, virtuelle Umgebungen, lokale `.env`- und Betriebsdaten)
nicht versionieren und generierte Dateien nicht von Hand bearbeiten.

Ein Auftrag ist fertig, wenn Implementierung, Migration/Konfiguration,
Fehlerbehandlung, Tests und Dokumentation zusammenpassen. Commit oder Push erfolgen
nur auf ausdrücklichen Wunsch; niemals fremde Historie umschreiben.
