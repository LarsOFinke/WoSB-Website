# Build Designer: Waffenvalidierung & Special Crew

Der Build Designer wurde um zwei harte Katalogbereiche erweitert:

## Special Crew

Special-Crew-Optionen sind normale Build-Optionen der Kategorie `special_crew`, besitzen aber eigene `stat_effects` und werden in `build_item_effects` normalisiert gespeichert. Dadurch fließen Crew-Spezialisten in dieselbe Stat-Berechnung ein wie Upgrades, ohne zusätzliche Sonderlogik im Frontend.

Aktuell sind die Effekte bewusst als konservative Prototyp-/Planungswerte markiert (`source = prototype/planning`). Sobald ein offizieller Export oder ein geprüftes Sheet vorliegt, müssen nur die Seedwerte angepasst werden.

## Waffen-Metadaten

Waffen besitzen zusätzliche Metadaten in `build_item_options`:

- `option_kind`
- `allowed_slot_types`
- `weapon_caliber_inches`

Damit kann das Backend prüfen, ob eine ausgewählte Waffe zum Slot passt:

- normale Kanonen: Front, Heck, Backbord, Steuerbord
- Bug-/Heckwaffen und Bombards: Front und Heck
- Mörser: nur dedizierter Mörser-Slot

## Schiffskapazitäten

Schiffe leiten ihre Waffenpositionen aus `ships.weapon_layout` ab. Unterstützte Layouts:

- `front-broadside-rear`, z. B. `2-38-4`
- `mortar 10in x2`
- kombinierte Layouts wie `1-22-0 + mortar 11in x2`

Daraus werden API-Felder abgeleitet:

- `front_weapon_capacity`
- `broadside_weapon_capacity`
- `rear_weapon_capacity`
- `mortar_weapon_capacity`
- `max_mortar_caliber_inches`

## Servervalidierung

`build_service.create_build()` validiert jetzt serverseitig:

- Waffenoption muss existieren und aktiv sein.
- Waffe muss zur Kategorie `weapon` gehören.
- Waffe muss den Slot-Typ erlauben.
- Mörser dürfen nur in `mortar_weapon_slots` liegen.
- Nicht-Mörser dürfen nicht in den Mörser-Slot.
- Mörserkaliber darf das Schiffslimit nicht überschreiten.
- Waffenanzahl darf die Kapazität der Schiffposition nicht überschreiten.
- Doppelte Waffen pro Slotgruppe müssen zusammengefasst werden.

## Frontend-Verhalten

Das Frontend filtert die Waffen-Dropdowns bereits nach Schiff und Slot. Die Backendvalidierung bleibt trotzdem verbindlich, weil UI-Filter allein keine Datenintegrität garantieren.

## Demo- und Seed-Checks

`build_catalog_quality.py` prüft zusätzlich:

- doppelte Waffen-/Crew-Namen
- ungültige Slot-Typen
- Mortar-Metadaten
- leere Special-Crew-Effekte

Demo-Builds enthalten jetzt auch ein Mörser-Beispiel, damit der Slot im Prototyp sichtbar und testbar ist.
