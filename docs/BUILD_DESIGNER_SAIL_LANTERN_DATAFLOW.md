# Build-Designer: verifizierte Segel- und Laternenwerte

## Datenquelle

Der Katalog basiert auf den vom Projektinhaber bereitgestellten In-Game-Tooltip-Screenshots. Die Werte werden als normalisierte Effekte gespeichert und von Frontend und Backend identisch ausgewertet.

```text
Seed-Katalog
→ build_item_options / build_item_effects
→ GET /api/builds/options
→ Live-Rechner
→ POST /api/builds
→ serverseitige Neuvalidierung
→ gespeicherte ship_stats
```

## Segel

Der erste Wert jedes Segels wird als absoluter Geschwindigkeitsbonus in Knoten gerechnet. Bedingte Reiseeffekte werden separat angezeigt und nicht dauerhaft auf den Basiswert des Schiffes aufgeschlagen.

| Segel | Effekte |
| --- | --- |
| Cheap Sails | `+2 kn` Geschwindigkeit |
| Stitched Sails | `+2,4 kn` Geschwindigkeit |
| Ultra-light Sails | `+2,4 kn` Geschwindigkeit, `+15 %` Wendigkeit im Reisemodus, `-30 %` Geschwindigkeit beim Wenden im Reisemodus |
| Storm Sails | `+2,7 kn` Geschwindigkeit, `+2,5 kn` Reisegeschwindigkeitsbonus bei starkem Wind |
| Elite Sails | `+2,8 kn` Geschwindigkeit |
| Tacking Sails | `+2,8 kn` Geschwindigkeit, `+2 kn` Reisegeschwindigkeitsbonus nach dem Wenden, `-20 %` Wendigkeit im Reisemodus |
| Reefed Sails | `+2,9 kn` Geschwindigkeit, `-100 %` Geschwindigkeitsbonus vor dem Wind, `-50 %` Reisegeschwindigkeitsbonus auf raumem Kurs |
| Tarpaulin Sails | `+3,1 kn` Geschwindigkeit, `-2` Wendigkeit |
| Raiding Sails | `+4,1 kn` Geschwindigkeit, `-20 %` Wendigkeit im Reisemodus, `-20 %` Reisegeschwindigkeits-Zuwachs |

## Laternen

| Laterne | Effekte |
| --- | --- |
| Blue Lantern | `+6 %` Geschwindigkeit |
| Bright Lantern | `+12 %` Laderaum |
| Golden Lantern | `+5 %` Geschwindigkeit, Panzerung und Schaden |
| Green Lantern | `+7 %` Haltbarkeit |
| Lilac Lantern | `+7 %` Wendigkeit |
| Red Lantern | `+5 %` Wendigkeit, `+5 %` Schaden, `+7 %` Erfahrung/Beute |
| White Lantern | `+10 %` Erfahrung/Beute |
| Yellow Lantern | `+7 %` Schaden |

## Rechenregeln

- `speed_knots` wird absolut zur Schiffsgeschwindigkeit addiert.
- `speed_pct`, `armor_pct`, `hull_hp_pct`, `turn_rate_pct` und `hold_capacity_pct` werden prozentual auf den jeweiligen Basiswert angewendet.
- `damage_pct` und `exp_loot_pct` sind eigenständige Effektwerte ohne Schiffsbasiswert.
- Bedingte Segeleffekte wie starker Wind oder Wenden werden als eigene Live-Effektzeilen angezeigt.
- Frontend und Backend erhalten dieselben Stat-Definitionen über die Build-Optionen-API.

## Seed- und Upgrade-Verhalten

Der Seed-Lauf prüft Anzahl, stabile `seed_id`, Effekt-Schlüssel und exakte Tooltip-Werte. Alte, nicht mehr aktive Katalogeinträge werden nur deaktiviert; bestehende Builds behalten ihre Referenzen.

Bewusste Admin-Overrides bleiben geschützt. Soll ein überschriebener Eintrag wieder die neuen Defaults erhalten, im Stammdaten-Admin **Seed-Standard wiederherstellen** verwenden.

## Rollout

Eine Schema-Migration ist nicht erforderlich. Der Seed-Lauf ist erforderlich:

```bash
sudo ./update.sh --seed
```

Beim Deployment aus einem ZIP:

```bash
sudo ./update.sh --skip-pull --seed
```

Der Admin-Button **Update + Migration + Seed** ist ebenfalls geeignet.
