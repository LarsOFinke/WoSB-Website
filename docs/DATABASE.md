# Datenbank und Stammdaten

## Produktionsschema

PostgreSQL ist die einzige Produktionsdatenbank. Alembic ist die alleinige Quelle für
Schemaänderungen; `create_all()` bleibt auf lokale SQLite-Tests beschränkt.

Im Hybridbetrieb bleibt Alembic der einzige Schema-Eigentümer. Die Spring-Security-API greift auf
`users`, `user_profiles`, `site_roles` und `auth_sessions` zu und startet ausschließlich mit
`spring.jpa.hibernate.ddl-auto=validate`. JPA- oder Flyway-Schemaerzeugung ist untersagt. Eine
spätere Übergabe der Schemahoheit benötigt eine eigene dokumentierte Migration und darf nicht
implizit durch Hibernate erfolgen.

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

Auch freischaltbare Build-Funktionen sind normalisiert. Ein Build speichert für den
Upgrade-Add-on-Slot ausschließlich `research_upgrade_feature_id`. Die Definition in
`build_features` enthält die Anzahl zusätzlicher Slots; jede statistische Auswirkung liegt als
eigene Zeile in `build_feature_effects`. Der aktuelle Katalog definiert einen zusätzlichen Slot
sowie jeweils `-5 %` Haltbarkeit, Manövrierfähigkeit und Laderaum. Berechnung und Anzeige lesen
diese Zeilen zur Laufzeit; die Werte sind nicht in Python- oder JavaScript-Formeln eingebettet.

Die Standard-Waffenklasse neuer Schiffe wird ebenfalls referenziell über
`ship_rate_weapon_class_rules` bestimmt: Rate 7–5 → Light, Rate 4–3 → Medium und Rate 2–1 →
Heavy. Die Regel gilt nur für reguläre Bug-, Heck- und Breitseiten-Mounts. Mörser und spezielle
Waffen sind ausgeschlossen. Ein expliziter Mount-Wert bleibt für geprüfte Schiffsausnahmen
erlaubt. Migration `0008` ergänzt die Klasse außerdem bei bereits gespeicherten regulären Mounts,
wenn deren Klasse leer und deren Kapazität größer als null ist; vorhandene Werte werden nie
überschrieben.

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
unter `backend/seeds/`. Das Manifest deckt Systemrollen, Flotten, normalisierte Build-Regeln,
Build-Kategorien und -Optionen sowie den nach Rate gegliederten Schiffskatalog ab. Unter
`backend/src` verbleiben nur Loader und idempotente Synchronisationslogik.

Die Staff-Stammdatenverwaltung bearbeitet Stat-Effekte nicht als freies JSON. Sie bezieht
Bezeichnung, Kategorie, Einheit, Genauigkeit und Werttyp aus dem zentralen Build-Statkatalog und
überträgt intern weiterhin den stabilen `stat_effects`-API-Vertrag. Damit bleiben technische
Schlüssel von der Oberfläche getrennt und schiffsspezifische Overrides verwenden dieselben
Ingame-Bezeichnungen wie die Build-Anzeige.

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
# Öffentliche Build-Printouts

Ein Build speichert höchstens ein veröffentlichtes PNG unter der stabilen URL
`/api/builds/<id>/printout`. `builds.printout_checksum` hält den SHA-256-Wert,
`printout_size_bytes` die Größe und `printout_updated_at` den letzten tatsächlichen
Inhaltswechsel. Ein identischer erneuter Upload schreibt die Datei nicht neu. Ein
geändertes Printout ersetzt dieselbe Datei atomar; beim Löschen des Builds wird sie
entfernt. Migration `0023_build_printouts` ergänzt ausschließlich diese Metadaten.

Weitere build-eigene Dateien werden über `build_file_attachments` eindeutig einem Build
zugeordnet. Beim Löschen prüft der Build-Service diese Zuordnungen und entfernt nach dem
erfolgreichen Datenbank-Commit sowohl die `stored_files`-Datensätze als auch die konkreten
Dateien. Gemeinsam genutzte Stammdaten- und Katalogbilder besitzen keine solche Zuordnung und
bleiben unberührt. Ist eine zugeordnete Datei zusätzlich mit einem anderen Build, einem Guide
oder einem Forumbeitrag verbunden, wird nur die Build-Zuordnung entfernt und die gemeinsam
genutzte Datei bleibt erhalten. Migration `0024_build_file_attachments` führt diesen Löschvertrag ein.

Der gleiche Löschvertrag gilt für Guide-Anhänge und Dateien an Forumbeiträgen: Beim Löschen
eines Guides werden seine Datei- und Build-Zuordnungen entfernt; beim Löschen eines Beitrags
oder eines vollständigen Threads werden dessen Dateizuordnungen entfernt. Eine Datei ohne
verbleibende Build-, Guide- oder Forum-Zuordnung wird anschließend aus `stored_files` und vom
Datenträger gelöscht. Bereichsübergreifend gemeinsam verwendete Dateien bleiben bestehen.

Migration `0025_security_signal_reasons` ergänzt die kurzlebigen IP-Sperrsignal-Aggregate um
eine feste Begründung und ein datensparsames Request-Ziel. Bestehende Zähler werden als historische
Aggregate ohne Detailziel markiert; neue Einträge unterscheiden sichere Routen-Templates und feste
Scan-Kategorien.

Die Veröffentlichung ist eine bewusste Aktion des Build-Eigentümers oder der
Moderation. Das Bild ist danach ohne Anmeldung lesbar und kann deshalb auch von
Discord abgerufen werden; Freitext im Build darf folglich keine vertraulichen oder
personenbezogenen Inhalte enthalten.
