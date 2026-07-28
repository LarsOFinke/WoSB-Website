# Build calculation audit

Audit date: 2026-07-28

## Calculation contract

The Build Designer uses one versioned cross-runtime contract in
`contracts/build-calculation-cases.json`. Backend and frontend tests execute the
same cases.

The verified order is:

1. Read the immutable ship base value.
2. Stack percentage effects from separate installed items multiplicatively.
3. Apply the resulting percentage to the configured base field.
4. Add flat effects after the percentage calculation.
5. Round only the presented/effective result with decimal half-up rounding.

For cruise maximum speed, percentage bonuses use the ship's minimum speed as
the percentage base, while flat sail speed is added to the cruise maximum.

## Verified Zeven case

`De Zeven Provincien` has a seeded speed range of `7.7–10.6 kn`. `Raiding
Sails` adds a flat `4.1 kn`, therefore:

```text
10.6 kn + 4.1 kn = 14.7 kn
```

`First Mate` does **not** change ship speed. Its tooltip is `+0.2% sail
deployment speed per assigned Sailor`; with 102 Sailors this becomes a separate
`+20.4% sail deployment speed` row. The historical `16.3 kn` result came from
mapping that operational effect to the unrelated ship-wide `speed_pct`:

```text
10.6 kn + (7.7 kn × 20.4%) + 4.1 kn = 16.2708 kn → 16.3 kn
```

The raw seed key and the calculated key are now explicitly separated as
`sail_deployment_speed_per_sailor_pct` and `sail_deployment_speed_pct`.

## Consistency fixes

- Composite percentage and flat modifiers retain both components instead of
  displaying a dimensional delta as a percentage.
- Crew capacity, sailing efficiency, specialist effects, backend validation,
  saved build statistics and live frontend previews share decimal half-up
  rounding.
- Positive and negative ties use the same half-away-from-zero behavior in
  Python and JavaScript.
- Every numeric effect key present in the seed catalog must have a declarative
  stat definition. The audit currently covers 106 seeded effect keys.

## Regression cases

The shared contract currently covers:

- De Zeven Provincien with Raiding Sails (`14.7 kn`),
- multiplicatively stacked speed/armor effects,
- percentage-before-flat durability,
- crew-capacity rounding at an exact `.5` boundary.
