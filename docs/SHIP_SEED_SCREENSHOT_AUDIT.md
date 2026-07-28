# Build Designer ship catalog audit

## Owned-ship batches — 2026-07-28 and 2026-07-29

The repository now contains **230 in-game screenshots** documenting all **38 ships currently owned by the contributor**. Every documented ship includes its statistics panel. The 37 ships with an upgrade rack also include their available upgrade groups; Balloon exposes no upgrade rack and therefore has only a statistics capture. Adventure, Eagle, Golden Apostle, Kobukson, La Royale, Red Arrow and Sovereign additionally include the mortar-upgrade group.

Audited ships:

- Rate I: 12 Apostolov, De Zeven Provincien, Huracan, La Couronne, La Royale, Santisima Trinidad, Sovereign, Victory
- Rate II: Adventure, Firestorm, Ingermanland, La Sirene, Neptuno, Redoutable, Sans Pareil, Vasa
- Rate III: Anson, Azov, Bellona, Kobukson, Mordaunt, Poltava
- Rate IV: Constitution, Devourer, Essex, Flying Cloud, Red Arrow
- Rate V: Black Prince, Eagle, La Creole, Russia, San Martin
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
| Red Arrow | cruise maximum 11.3 kn |
| Redoutable | cruise maximum 10.0 kn |
| Russia | speed range 10.4–12.5 kn; armor 2.8 |
| Santisima Trinidad | cruise maximum 9.4 kn |
| Sans Pareil | cruise maximum 10.6 kn; maneuverability 78 |
| Savannah | cruise maximum 12.8 kn |
| Shunsen | cruise maximum 11.2 kn |
| Sovereign | cruise maximum 10.4 kn |
| Vasa | cruise maximum 9.6 kn |
| Victory | cruise maximum 10.1 kn |

Values not listed above already matched the repository catalog and were retained. The first 33 records carry the provenance `WoSB in-game owned-ship screenshot audit 2026-07-28`; 12 Apostolov, Balloon, Flying Cloud, Huracan and La Royale carry `WoSB in-game owned-ship screenshot audit 2026-07-29`.

## Upgrade-slot interpretation

The upgrade-capable screenshots show six ordinary upgrade spaces on most ships, seven on La Couronne and seven on Huracan. The account also displays a researched `Spaces for upgrades +1` benefit. Therefore the screenshots contain one account-level slot in addition to the ship base value. The seed catalog correctly retains five configured slots for ordinary ships and six for La Couronne and Huracan.

Balloon explicitly displays `Upgrades -`. It is seeded with zero upgrade slots, and the slot-access service prevents research or Structural Expansion effects from creating an upgrade rack on a ship that has none.

The unlabelled `0/4` indicator is treated as player/account state rather than a ship property and is not seeded.

## Mortar interpretation

Adventure, Golden Apostle and Sovereign expose explicit mortar capacities in their ship statistics and remain modeled accordingly. Eagle, Kobukson and Red Arrow show the mortar upgrade category, but the supplied panels do not quantify a modification delta. Their existing audited weapon layouts are therefore unchanged. A future change requires a dedicated screenshot showing the complete before/after modification values; the catalog does not infer capacities from upgrade-category visibility alone.

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
