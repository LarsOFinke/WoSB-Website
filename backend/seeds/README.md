# JSON-Stammdaten

Dieses Verzeichnis ist die einzige Quelle für repository-eigene Stammdaten.
Unter `backend/src` liegen keine Datensätze mehr: Dort verbleiben ausschließlich
strikte Validierung, idempotente Datenbank-Synchronisation und das
umgebungsbasierte Bootstrap des ersten Administratorkontos.

## Struktur

```text
seeds/
├── manifest.json
├── references.json
├── system/
│   ├── roles.json
│   └── fleets.json
├── builds/
│   ├── categories.json
│   └── options/
│       ├── sails.json
│       ├── upgrades.json
│       ├── lanterns.json
│       ├── ammunition.json
│       ├── consumables.json
│       ├── hold.json
│       ├── weapons.json
│       └── specialists.json
└── ships/
    ├── definitions.json
    └── rates/
        ├── rate-1.json
        └── … rate-7.json
```

`manifest.json` listet jedes JSON-Dokument mit seinem Typ auf. Nicht gelistete,
fehlende oder doppelt eingetragene Dateien brechen den Ladevorgang ab. Damit
kann keine neue Datei unbemerkt neben dem tatsächlich geladenen Katalog liegen.

Jedes Dokument besitzt `schema_version` und `catalog`. Unbekannte Felder,
ungültige Typen, doppelte IDs und widersprüchliche Referenzen werden vor der
ersten Datenbankänderung abgewiesen.

## Wartungsregeln

- `seed_id` ist die dauerhafte technische Identität. Eine Umbenennung ändert
  nur `name`, niemals `seed_id`.
- Jede Build-Option gehört in genau eine Datei unter `builds/options`.
- Umbenannte Upgrade-Bezeichnungen werden über `aliases` in `upgrades.json`
  migriert, damit bestehende Builds verbunden bleiben.
- Neue Schiffe werden in die Datei ihrer Rate eingetragen.
- Neue JSON-Dateien werden zusätzlich im Manifest registriert.
- Geheimnisse und installationsabhängige Werte gehören nicht in diesen
  Katalog. Das initiale Administratorkonto kommt weiterhin aus der Umgebung.
- Produktionsläufe bleiben idempotent: unveränderte Datensätze werden nicht
  neu geschrieben, Admin-Overrides bleiben geschützt und entfernte Defaults
  werden deaktiviert statt gelöscht.

## Schiffe und Waffen-Mounts

`ships/definitions.json` enthält die normalisierten Waffenklassen und Slottypen.
Jedes Schiff definiert genau sechs Mounts, auch wenn deren `capacity` null ist:

- `weapon_front`: Bugwaffen
- `weapon_rear`: Heckwaffen
- `weapon_port`: Backbord-Breitseite
- `weapon_starboard`: Steuerbord-Breitseite
- `weapon_mortar`: Mörser und Fasswerfer
- `weapon_special`: optionaler dedizierter Spezialwaffen-Mount

`special_weapon_capacity` ist eine Obergrenze innerhalb der normalen
`capacity`. Spezialwaffen sind nur an Bug, Heck oder einem dedizierten
Spezialmount erlaubt. Ein bestückbarer Mörser-Mount benötigt zusätzlich
`max_caliber_inches`.

`mortar_modification` bildet den permanenten Schiffsumbau ab und ist kein
normales Upgrade. `null` bedeutet, dass der Umbau nicht verfügbar ist. Aktuell
ist er für `Black Wind`, `Falmouth` und `Friede` hinterlegt. Das Build speichert
nur die Auswahl; Kapazitäten und Stat-Effekte stammen immer aus dem
Schiffskatalog.

## Ausführen

In Produktion werden Schema und Stammdaten bewusst getrennt behandelt:

```bash
sudo ./update.sh
sudo ./update.sh --seed
```

Der normale Lauf migriert nur das Schema. `--seed` führt zuerst die Migration
und anschließend die idempotente JSON-Synchronisation aus. Es werden keine
Beispiel-Builds, Guides, Termine oder Nutzeraktivitäten erzeugt.
