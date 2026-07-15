# Datenbank und Stammdaten

## Produktionsschema

PostgreSQL ist die einzige Produktionsdatenbank. Alembic ist die alleinige Quelle für
Schemaänderungen; `create_all()` bleibt auf lokale SQLite-Tests beschränkt.

Das Schema folgt der 3. Normalform: Rollen, Schiffe, Mounts, Präferenzen, Mitgliedschaften,
Katalogoptionen und Effekte besitzen eigene Tabellen und Fremdschlüssel. Historisch referenzierte
Stammdaten werden deaktiviert statt gelöscht.

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

Der Schiffskatalog ist nach Rate in `backend/src/app/seeds/ship_data/` gegliedert. Neue Schiffe werden über die gemeinsame `ship()`-Factory ergänzt; dadurch bleiben Standardwerte, Quellenkennzeichnung und das Planungsmodell für Mindestbesatzung konsistent.

```bash
sudo ./update.sh --seed
```

Der API-Container seedet beim normalen Start nicht automatisch. Setup und Updater starten dafür den
eigenen, kurzlebigen Seed-Container ausdrücklich.

## Backup und Restore

```bash
make infra-backup
./infrastructure/scripts/backup/restore-postgres.sh <dump-file>
```

Vor Migration oder Seed erstellt der Updater automatisch ein Sicherheitsbackup. Ein Restore wird
zuerst auf einer separaten Instanz geprüft.
