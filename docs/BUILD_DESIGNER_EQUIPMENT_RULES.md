# Build-Designer: Ausrüstungsregeln und Stat-Berechnung

## Grundsatz

Der Build-Designer berechnet Segel, Laternen, Upgrades, Spezialisten und die Forschungsbelohnung über dieselben normalisierten Effekt-Schlüssel. Frontend-Vorschau und Backend verwenden dieselbe Struktur; das Backend validiert Kapazitäten und Slots erneut.

Effekte werden in `build_item_effects` gespeichert. Seed-Daten liefern überarbeitbare Defaults. Änderungen unter **Admin → Stammdaten** werden als Override geschützt.

## Überprüfte Segel- und Laternenwerte

Frühere Prozentwerte für Segel und frei angenommene Laternenboni wurden entfernt. Sie waren keine belastbar geprüften Spielwerte.

Aktuell als exakter Tooltip-Wert hinterlegt:

| Ausrüstung | Effekt |
| --- | --- |
| Raiding Sails / Überfallsegel | `+4,1 kn` Geschwindigkeit und `-20 %` Reisegeschwindigkeits-Zuwachs |

Für Tarpaulin, Imported und Elite Sails sowie die zwölf Laternen bleiben die Effektobjekte leer, solange kein aktueller Tooltip-Nachweis vorliegt. Die Einträge bleiben auswählbar und über die Stammdatenverwaltung editierbar. So zeigt der Live-Rechner keine erfundenen Werte an.

Die Stat-Engine unterstützt dabei sowohl absolute Geschwindigkeitswerte (`speed_knots`) als auch Prozentwerte (`speed_pct`) und separate Werte wie `cruising_speed_gain_pct`.

## Laternenwechsel

Segel- und Laternen-Dropdowns zeigen keine redundante Stat-Zeile mehr. Die Auswahl bleibt ein normales `v-model`-Select und kann beliebig ersetzt oder geleert werden. Auswirkungen erscheinen ausschließlich im Live-Rechner.

## Zusätzlicher Upgrade-Slot

Ein Build besitzt das persistierte Flag `research_upgrade_slot_unlocked`. Wird die accountweite Forschungsbelohnung aktiviert, gelten neben dem zusätzlichen Slot automatisch folgende normalisierte Mali:

- Haltbarkeit `-10 %`
- Geschwindigkeit `-10 %`
- Manövrierbarkeit `-10 %`
- Panzerung `-10 %`
- Laderaum `-10 %`
- Crewkapazität `-10 %`

Die Mali wirken in der Live-Vorschau, in gespeicherten Build-Stats und in der serverseitigen Crewkapazitätsprüfung.

## Spezialisten

Der Projektkatalog enthält 24 aktive Spezialisten mit stabilen `seed_id`-Werten. Dadurch können Bezeichnungen später geändert werden, ohne gespeicherte Builds oder Admin-Overrides zu verlieren.

Die öffentlich verfügbaren B20-Hinweise bestätigen das Specialist-System, enthalten aber keine vollständige maschinenlesbare Liste mit aktuellen Namen und Effekten. Der Katalog ist deshalb ausdrücklich als projektgepflegter Stand markiert. Exakte Änderungen aus dem Spiel können über **Admin → Stammdaten** eingepflegt und anschließend mit derselben stabilen Seed-ID in den Seed übernommen werden.

## Waffen-Slots

Die Slot-Kompatibilität wird über `ship_weapon_mounts` und `build_item_option_slot_types` abgebildet.

- Barrel Launcher: ausschließlich Mörser-Slot
- Alchemical Fire und Imperial Bombard: ausschließlich Spezialwaffen-Mounts
- normale Front-, Heck- und Breitseiten-Slots: nur kompatible normale Waffen

## Migration und Rollout

Die Cookie-Erweiterung ergänzt die aktuelle Alembic-Kette bis:

```text
d4e5f6a7b8c9_cookie_consent.py
```

Deployment aus Git:

```bash
sudo ./update.sh --migrate --seed
```

Deployment aus einem ZIP ohne Git-Pull:

```bash
sudo ./update.sh --skip-pull --migrate --seed
```
