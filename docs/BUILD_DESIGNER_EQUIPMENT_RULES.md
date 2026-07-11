# Build-Designer: Ausrüstungsregeln und Stat-Berechnung

## Ziel

Der Build-Designer behandelt Ausrüstung nicht mehr nur als Anzeige- oder Inventarwert. Segel, Laternen, Upgrades und Spezialisten liefern ihre Effekte über dieselbe normalisierte Effektstruktur. Frontend-Vorschau und Backend-Berechnung nutzen dieselben Effekt-Schlüssel und validieren Slots serverseitig.

## Stat-Effekte

Effekte bleiben Stammdaten und werden in `equipment_option_effects` gespeichert. Der Seed liefert nur überarbeitbare Defaults. Änderungen über **Admin → Stammdaten** werden als Admin-Override geschützt und bei späteren Seed-Läufen nicht überschrieben.

Aktuelle Projekt-Defaults:

| Ausrüstung | Effekt |
| --- | --- |
| Tarpaulin Sails | Geschwindigkeit +2 % |
| Raiding Sails | Geschwindigkeit +4 % |
| Imported Sails | Geschwindigkeit +6 % |
| Elite Sails | Geschwindigkeit +8 % |
| Golden Lantern | Laderaum +1.000 |
| Ice Lantern | Panzerung +2 % |
| Red Lantern | Nachladegeschwindigkeit +3 % |
| Storm Lantern | Geschwindigkeit +3 % |

Die übrigen Laternen bleiben derzeit kosmetisch und besitzen bewusst keinen Stat-Effekt. Die Zahlen sind wartbare Projektwerte, keine als offiziell verifizierten Spielwerte. Sie können ohne Codeänderung über die Stammdatenverwaltung angepasst werden.

## Waffen-Slots

Die Slot-Kompatibilität wird über `ship_weapon_mounts` und `equipment_option_slot_types` abgebildet. Schiffsnamen werden nicht im Build-Service hart codiert.

- Normale Front-, Heck-, Backbord- und Steuerbord-Slots akzeptieren normale Waffen.
- Der Mörser-Slot akzeptiert `mortar` und `mortar_launcher`.
- Der Spezialwaffen-Slot akzeptiert ausschließlich `special_weapon`.
- `Barrel Launcher` ist `mortar_launcher` und ausschließlich dem Mörser-Slot zugeordnet.
- `Alchemical Fire` und `Imperial Bombard` sind Spezialwaffen und werden nur auf Schiffen mit einem `weapon_special`-Mount angeboten.
- Huracan besitzt im Seed zwei Spezialwaffenplätze; Deadfish besitzt einen.

Die API prüft diese Regeln erneut. Manipulierte Frontend-Payloads können daher keine unzulässige Waffe speichern.

## Zusätzlicher Upgrade-Slot

Ein Build besitzt das persistierte Flag `research_upgrade_slot_unlocked`. Der Nutzer aktiviert es im Designer, wenn die accountweite Forschungsbelohnung freigeschaltet ist.

Die Slotberechnung unterscheidet unabhängige Freischaltungen:

1. Basis-Slots des Schiffs
2. Forschungsbelohnung
3. `extra_upgrade_slots` aus ausgewählten Upgrades

Damit kann Slot 5 durch eine der Freischaltungen geöffnet werden. Slot 6 ist verfügbar, wenn das Schiff ihn bereits besitzt oder zwei unabhängige zusätzliche Freischaltungen zusammenkommen. Dieselbe Berechnung wird im Frontend und Backend verwendet; das Backend bleibt maßgeblich.

## Migration und Rollout

Migration:

```text
c3d4e5f6a7b8_build_designer_equipment_rules.py
```

Sie ergänzt `builds.research_upgrade_slot_unlocked` mit einem sicheren Standardwert `false`. Für bestehende Builds ändert sich dadurch nichts.

Deployment aus einem Git-Checkout:

```bash
sudo ./update.sh --migrate --seed
```

Deployment aus einem entpackten ZIP ohne Git-Pull:

```bash
sudo ./update.sh --skip-pull --migrate --seed
```
