# Upgrade seed screenshot audit

## Scope

The global upgrade catalog contains **32 active upgrades**. Upgrade definitions remain normalized and reusable; only numeric values that visibly differ for a particular ship are stored as sparse rows in `ship_upgrade_effect_overrides`.

The owned-ship screenshot batch from 2026-07-28 demonstrates three value sets for six upgrades:

| Upgrade | Rates I–II | Rates III–IV global default | Rates V–VI |
|---|---:|---:|---:|
| Reinforced Masts — speed | +0.4 kn | +0.5 kn | +0.6 kn |
| Reinforced Masts — sail efficiency | +0.8 | +1.0 | +1.2 |
| Double Hold — hold | +6500 | +4500 | +3000 |
| Cellars — hold | +3500 | +2000 | +1500 |
| Extra Bunks — crew | +20 | +14 | +10 |
| Repair Arsenal — durability | +210 | +150 | +80 |
| Teak Frames — armor | +1.0 | +1.5 | +2.0 |
| Teak Frames — crew | +14 | +10 | +6 |

All percentage, boolean and secondary effects shown in the screenshots match the global definition and continue to be inherited. No value is extrapolated to an unscreenshoted ship: sparse overrides are included only for the 19 owned rate I–II and V–VI ships. The nine owned rate III–IV ships use the verified global defaults. Rate VII retains the global catalog until a direct ship-specific capture is available.

## Verified global defaults

### Speed

| Upgrade | Default effects |
|---|---|
| Maneuverable Helm | Maneuverability +8%; cruise-speed turning speed -15% |
| Reinforced Masts | Speed +0.5 kn; additional sail efficiency +1 |
| Lightweight Hull | Maneuverability +5%; speed +4%; armor -15% |

### Expeditionary

| Upgrade | Default effects |
|---|---|
| Small Hooks | Reeling speed +250%; fishing speed +30%; boarding range +15% |
| Combat Crow's Nest | Visibility range +50%; weapon aiming speed +60% |
| Sturdy Frames | Durability +10%; hold +12%; speed -15% |
| Double Hold | Hold +4500; item loss -40%; durability -5% |
| Extra Ballast | Ship-roll reduction +50%; weapon spread -40% |
| Cellars | Hold +2000; perishable goods do not spoil |
| Extra Bunks | Crew +14; crew count hidden |

### Protection

| Upgrade | Default effects |
|---|---|
| Repair Arsenal | Durability +150; repair-item efficiency +20% |
| Iron Plating | Water-fire protection +45%; armor -10% |
| Copper Plating | Water-fire protection +25%; gunpowder-barrel and fire-ship protection +30% |
| Iron Ram | Ram damage +20%; bow damage absorption +20%; quick sinking by ramming |
| Reinforced Bolt Ropes | Sail protection +30%; sail-fire protection +50% |
| Teak Frames | Armor +1.5; crew +10; maneuverability -6% |

### Combat

| Upgrade | Default effects |
|---|---|
| Upper Deck | Barrel reload +35%; swivel-gun reload +35% |
| Ammunition Cradles | Reload speed +12% |
| Advanced Gun Carriages | Weapon angle +10; weapon aiming speed +30% |
| Reinforced Cannons | Bow and stern weapon damage +87% |
| Incendiary Mixture | Fire/ignition with every ammunition type; projectile speed +10% |
| Fortified Ports | Cannon range +10 |
| Combat Arsenal | Item reload +20%; ammunition-type switch speed +50% |

### Unusual

| Upgrade | Default effects |
|---|---|
| Strong Beams | Durability +5%; mortar protection +30%; speed -5% |
| Portable Chest | Successful boarding grants +5% gold |
| Emergency Powder Charge | Damage scales from +10% to +25%, max at 33% durability |
| High Helm Port | Barrels/mines usable at third speed; damage radius +30% |
| Structural Expansion | Upgrade spaces +2; maneuverability -10% |

### Mortar

| Upgrade | Default effects |
|---|---|
| Long-Range Mortars | Mortar range +10; maneuverability -8% |
| Reinforced Centre-Line | Mortar aiming +40%; dead-zone reduction +30% |
| Lightweight Construction | Mortar reload +40%; hold +25%; mortar damage -25% |
| Swivel Mortars | Mortar damage +12%; mortar angle +50°; mortar aiming -25% |

## Synchronization behavior

- Ship JSON documents contain only the effects that differ from the global option.
- The bootstrap resolves references by stable upgrade `seed_id`, never by display name.
- Administratively overridden ships are not changed by later seed runs.
- Restoring a ship seed reinstates its screenshot-backed sparse values.
- Renamed global options continue to preserve saved build and override references.
