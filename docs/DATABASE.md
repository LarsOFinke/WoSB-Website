# Datenbank und Stammdaten

## Produktionsschema

PostgreSQL ist die einzige Produktionsdatenbank. Alembic ist die alleinige Quelle für
Schemaänderungen; `create_all()` bleibt auf lokale SQLite-Tests beschränkt.

Das Schema folgt der 3. Normalform: Rollen, Schiffe, Mounts, Präferenzen, Mitgliedschaften,
Katalogoptionen und Effekte besitzen eigene Tabellen und Fremdschlüssel. Historisch referenzierte
Stammdaten werden deaktiviert statt gelöscht.

### Builds: Referenzen statt Ergebnis-Snapshots

Gespeicherte Builds enthalten ausschließlich vom Nutzer eingegebene Daten und normalisierte
Referenzen: `ship_id`, `option_id`, Slotpositionen, Mengen, Crewverteilung und Freitext.
Berechnete Werte wie Geschwindigkeit, Haltbarkeit, Rüstung, Kapazitäten, Buffs oder Warnungen
werden **nicht** in `builds` oder `build_slots` gespeichert. Die API erzeugt `ship_stats` bei jedem
Lesen aus den aktuell referenzierten Schiffen, Optionen, Effekten und schiffsspezifischen
Overrides. Dadurch übernehmen auch ältere Builds korrigierte Stammdaten automatisch, ohne dass
sie erneut gespeichert oder angelegt werden müssen.

Ein Repository-Gate prüft die zulässigen Spalten beider Build-Tabellen, und ein Integrationstest
ändert nach dem Speichern eines Builds dessen Schiff-/Segel-Stammdaten und verifiziert die
unmittelbare Neuberechnung desselben Datensatzes. Ergebnis-Snapshots sind bewusst verboten.

## Migrationen

```bash
cd backend
alembic revision --autogenerate -m "beschreibung"
alembic upgrade head
alembic check
```

Die historische Migrationskette wurde in `0001_baseline` aufgelöst. Diese Baseline bildet das
aktuelle SQLAlchemy-Modell vollständig ab und ist der einzige Startpunkt für neue Datenbanken.
Neue Schemaänderungen werden ab jetzt wieder als kleine, fachlich fokussierte Migrationen ergänzt.

**Wichtig:** Die Baseline ist bewusst kein In-Place-Upgradepfad für ältere Installationen. Vor dem
Wechsel von einer historischen Datenbank muss ein vollständiges Backup und ein geprüfter
Datenexport/-import in eine frisch mit `0001_baseline` erzeugte Datenbank erfolgen. Ein bloßes
`alembic stamp` ersetzt diese Prüfung nicht.

## Produktions-Seeds

Der v1-Seed enthält ausschließlich:

- Rollen- und Berechtigungskatalog
- initiales Administratorkonto
- notwendige Flotten-Systemdatensätze
- Waffen-, Schiff- und Build-Designer-Stammdaten

Er erzeugt **keine** Beispiel-Builds, Guides, Beiträge, Gruppen, Termine, Dateien oder künstliche
Nutzeraktivität. Solche Daten existieren nur als isolierte Test-Fixtures.

Seed-Datensätze besitzen stabile Identität, Revision, Checksumme und Override-Status. Identische
Läufe schreiben nichts neu; Admin-Overrides bleiben geschützt; entfernte Defaults werden inaktiv.

Alle repository-eigenen Stammdaten liegen als streng validierte JSON-Dokumente
unter `backend/seeds/`. Das Manifest deckt Systemrollen, Flotten, Build-Kategorien
und -Optionen sowie den nach Rate gegliederten Schiffskatalog ab. Unter
`backend/src` verbleiben nur Loader und idempotente Synchronisationslogik.

```bash
sudo ./update.sh --seed
```

`--seed` führt immer zuerst `alembic upgrade head` aus. Der API-Container seedet beim normalen Start
nicht automatisch. Setup und Updater starten dafür den eigenen, kurzlebigen Seed-Container
ausdrücklich.

## Backup und Restore

```bash
make infra-backup
sudo ./infrastructure/scripts/backup/restore-postgres.sh <dump-file>
```

Vor Migration oder Seed erstellt der Updater automatisch ein Sicherheitsbackup. Der
Produktions-Restore erstellt zusätzlich ein Pre-Restore-Backup, sperrt parallele Updates, stoppt API
und Gateway, beendet aktive Datenbankverbindungen, spielt den Dump ein, migriert auf den aktuellen
Alembic-Head und startet die Anwendung erst nach erfolgreicher Readiness-Prüfung wieder. Ein Restore
wird trotzdem zuerst auf einer separaten Instanz geprüft.
