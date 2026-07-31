# Build Designer ship catalog audit

## Owned-ship batches — 2026-07-28, 2026-07-29 and 2026-07-31

The repository now contains **254 in-game ship screenshots** documenting all **41 ships currently owned by the contributor**. Every documented ship includes its statistics panel. The 40 ships with an upgrade rack also include their available upgrade groups; Balloon exposes no upgrade rack and therefore has only a statistics capture. Adventure, Black Wind, Eagle, Golden Apostle, Kobukson, La Royale, Prins Willem, Red Arrow, Sovereign and Sparrow additionally include the mortar-upgrade group. Black Wind also includes the quantified mortar-fitting modification panel.

Audited ships:

- Rate I: 12 Apostolov, De Zeven Provincien, Huracan, La Couronne, La Royale, Santisima Trinidad, Sovereign, Victory
- Rate II: Adventure, Firestorm, Ingermanland, La Sirene, Neptuno, Redoutable, Sans Pareil, Vasa
- Rate III: Anson, Azov, Bellona, Kobukson, Mordaunt, Poltava, Prins Willem
- Rate IV: Constitution, Devourer, Essex, Flying Cloud, Red Arrow, Sparrow
- Rate V: Black Prince, Black Wind, Eagle, La Creole, Russia, San Martin
- Rate VI: Balloon, Golden Apostle, Le Cerf, Mercury, Savannah, Shunsen

The following values were updated from the displayed panels:

| Ship | Updated values |
|---|---|
| 12 Apostolov | cruise maximum 9.2 kn |
| Adventure | cruise maximum 11.0 kn |
| Anson | cruise maximum 11.0 kn |
| Azov | cruise maximum 10.6 kn |
| Balloon | cruise maximum 23.0 kn; no upgrade rack |
| Black Prince | cruise maximum 12.2 kn |
| Black Wind | cruise maximum 11.8 kn; small-ship Reinforced Masts, hold, bunk, repair and Teak Frames values; Reinforced Cannons +100%; mortar-fitting deltas verified |
| Constitution | cruise maximum 10.9 kn |
| Devourer | cruise maximum 10.5 kn |
| Eagle | cruise maximum 11.8 kn |
| Essex | cruise maximum 11.5 kn |
| Firestorm | cruise maximum 11.3 kn |
| Flying Cloud | cruise maximum 13.3 kn |
| Golden Apostle | cruise maximum 11.9 kn |
| Huracan | cruise maximum 8.5 kn |
| Ingermanland | cruise maximum 11.6 kn |
| Kobukson | cruise maximum 10.9 kn |
| La Couronne | cruise maximum 10.6 kn |
| La Creole | cruise maximum 12.9 kn |
| La Royale | cruise maximum 10.4 kn |
| La Sirene | cruise maximum 10.9 kn |
| Le Cerf | cruise maximum 12.2 kn |
| Mercury | cruise maximum 11.7 kn |
| Mordaunt | speed range 9.1–11.6 kn; armor 4.1 |
| Neptuno | cruise maximum 11.0 kn |
| Poltava | cruise maximum 12.0 kn |
| Prins Willem | cruise maximum 11.2 kn; Reinforced Cannons +74% |
| Red Arrow | cruise maximum 11.3 kn |
| Redoutable | cruise maximum 10.0 kn |
| Russia | speed range 10.4–12.5 kn; armor 2.8 |
| Santisima Trinidad | cruise maximum 9.4 kn |
| Sans Pareil | cruise maximum 10.6 kn; maneuverability 78 |
| Savannah | cruise maximum 12.8 kn |
| Shunsen | cruise maximum 11.2 kn |
| Sovereign | cruise maximum 10.4 kn |
| Sparrow | cruise maximum 11.6 kn; Reinforced Cannons +113% |
| Vasa | cruise maximum 9.6 kn |
| Victory | cruise maximum 10.1 kn |

Values not listed above already matched the repository catalog and were retained. The first 33 records carry the provenance `WoSB in-game owned-ship screenshot audit 2026-07-28`; 12 Apostolov, Balloon, Flying Cloud, Huracan and La Royale carry `WoSB in-game owned-ship screenshot audit 2026-07-29`; Black Wind, Prins Willem and Sparrow carry `WoSB in-game owned-ship screenshot audit 2026-07-31`.

## Upgrade-slot interpretation

The upgrade-capable screenshots show six ordinary upgrade spaces on most ships and seven on La Couronne, Huracan and Prins Willem. The account also displays a researched `Spaces for upgrades +1` benefit. Therefore the screenshots contain one account-level slot in addition to the ship base value. The seed catalog correctly retains five configured slots for ordinary ships, including Black Wind and Sparrow, and six for La Couronne, Huracan and Prins Willem.

Balloon explicitly displays `Upgrades -`. It is seeded with zero upgrade slots, and the slot-access service prevents research or Structural Expansion effects from creating an upgrade rack on a ship that has none.

The unlabelled `0/4` indicator is treated as player/account state rather than a ship property and is not seeded.

## Mortar interpretation

Adventure, Golden Apostle, Sovereign and Sparrow expose explicit mortar capacities in their ship statistics and remain modeled accordingly. Black Wind has no base mortar slot, but its dedicated fitting panel directly verifies the +1 mortar, -5 weapons per broadside, -180 durability, +15 maneuverability and -23 crew modification already represented by the catalog. Eagle, Kobukson, Prins Willem and Red Arrow show the mortar upgrade category without a quantified base slot or modification delta, so their existing audited weapon layouts remain unchanged. The catalog never infers mortar capacity from upgrade-category visibility alone.

## Catalog scope

The ship catalog contains **67 active seed records**. All records remain backed by supplied in-game panels or current-event tooltips. The Build Designer represents:

- name, rate and ship type
- durability, minimum and cruise-maximum speed, maneuverability and broadside armor
- hold and crew capacity
- planning sailor minimum and displacement
- sail, lantern and base upgrade-slot availability
- regular weapon class and explicit positional capacities
- quantified mortar and special-weapon capabilities
- sparse ship-specific upgrade-effect values where directly visible

Player resources, prices, ownership counts, unlock progress, port restrictions, inventory labels and other account state are intentionally excluded.
