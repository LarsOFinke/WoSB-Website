# Build Designer ship catalog audit

## Owned-ship batch — 2026-07-28

The repository now contains **204 in-game screenshots** documenting all **33 ships currently owned by the contributor**. Every documented ship includes its statistics panel and the available upgrade groups. Adventure, Eagle, Golden Apostle, Kobukson, Red Arrow and Sovereign additionally include the mortar-upgrade group.

Audited ships:

- Rate I: De Zeven Provincien, La Couronne, Santisima Trinidad, Sovereign, Victory
- Rate II: Adventure, Firestorm, Ingermanland, La Sirene, Neptuno, Redoutable, Sans Pareil, Vasa
- Rate III: Anson, Azov, Bellona, Kobukson, Mordaunt, Poltava
- Rate IV: Constitution, Devourer, Essex, Red Arrow
- Rate V: Black Prince, Eagle, La Creole, Russia, San Martin
- Rate VI: Golden Apostle, Le Cerf, Mercury, Savannah, Shunsen

The following values were updated from the displayed panels:

| Ship | Updated values |
|---|---|
| Adventure | cruise maximum 11.0 kn |
| Anson | cruise maximum 11.0 kn |
| Azov | cruise maximum 10.6 kn |
| Black Prince | cruise maximum 12.2 kn |
| Constitution | cruise maximum 10.9 kn |
| Devourer | cruise maximum 10.5 kn |
| Eagle | cruise maximum 11.8 kn |
| Essex | cruise maximum 11.5 kn |
| Firestorm | cruise maximum 11.3 kn |
| Golden Apostle | cruise maximum 11.9 kn |
| Ingermanland | cruise maximum 11.6 kn |
| Kobukson | cruise maximum 10.9 kn |
| La Couronne | cruise maximum 10.6 kn |
| La Creole | cruise maximum 12.9 kn |
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

Values not listed above already matched the repository catalog and were retained. All 33 records carry the provenance `WoSB in-game owned-ship screenshot audit 2026-07-28`.

## Upgrade-slot interpretation

The screenshots show six ordinary upgrade spaces on most ships and seven on La Couronne. The account also displays a researched `Spaces for upgrades +1` benefit. Therefore the screenshots contain one account-level slot in addition to the ship base value. The seed catalog correctly retains five base slots for ordinary ships and six for La Couronne.

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
