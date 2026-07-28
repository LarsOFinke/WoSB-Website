# Ship speed-range screenshot audit

> Historical filename retained for links. No unit conversion is applied.

The current ship panels display a minimum/base speed and, when the full range is available, a cruise maximum. The seed fields preserve those displayed values directly:

- `speed_min_knots`: left/minimum panel value
- `speed_knots`: right/cruise-maximum panel value

The earlier interpretation that the first number required an `m/s × 1.943844` conversion was incorrect and is no longer used.

## Owned-ship batch — 2026-07-28

| Rate | Ship | Minimum | Cruise maximum |
|---:|---|---:|---:|
| 1 | De Zeven Provincien | 7.7 | 10.6 |
| 1 | La Couronne | 7.6 | 10.6 |
| 1 | Victory | 7.1 | 10.1 |
| 2 | Adventure | 8.2 | 11.0 |
| 2 | Ingermanland | 9.0 | 11.6 |
| 2 | La Sirene | 8.1 | 10.9 |
| 2 | Neptuno | 8.2 | 11.0 |
| 2 | Redoutable | 7.0 | 10.0 |
| 2 | Sans Pareil | 7.7 | 10.6 |
| 2 | Vasa | 6.6 | 9.6 |
| 3 | Anson | 8.2 | 11.0 |
| 3 | Bellona | 7.5 | 10.5 |
| 3 | Kobukson | 8.0 | 10.9 |
| 3 | Mordaunt | 9.1 | 11.6 |
| 3 | Poltava | 9.6 | 12.0 |
| 4 | Constitution | 8.0 | 10.9 |
| 4 | Devourer | 7.5 | 10.5 |
| 4 | Essex | 8.9 | 11.5 |
| 4 | Red Arrow | 8.6 | 11.3 |
| 5 | Black Prince | 9.9 | 12.2 |
| 5 | Eagle | 9.4 | 11.8 |
| 5 | La Creole | 11.0 | 12.9 |
| 5 | Russia | 10.4 | 12.5 |
| 5 | San Martin | 8.5 | 11.2 |
| 6 | Golden Apostle | 9.5 | 11.9 |
| 6 | Le Cerf | 10.0 | 12.2 |
| 6 | Mercury | 9.2 | 11.7 |
| 6 | Shunsen | 8.5 | 11.2 |

**Directly re-audited in this batch:** 28 ships.

The remaining catalog records retain their previously audited values until a panel showing both endpoints is supplied. Tests prevent the newly captured ranges from regressing to the old single-value or converted interpretation.
