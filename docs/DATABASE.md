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

Jede Migration muss sowohl auf einer leeren Datenbank als auch als Upgrade des vorherigen Heads
funktionieren. Die v1-Migration `e5f6a7b8c9d0` entfernt bekannte, unveränderte 0.x-Beispieldaten,
ohne selbst erstellte Inhalte neu zu klassifizieren oder zu überschreiben.

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
