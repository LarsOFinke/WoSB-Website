# Spring API utility policy

This is the routing guide for reusable Java helpers in `spring-api`. Read it
before adding a local `now()`, `blank()`, formatter, or JDBC-row conversion
helper. The goal is one source of truth without turning `core` into a domain
miscellany package.

## Safe centralization candidates

### UTC timestamps

Many services currently repeat the same behavior:

```java
LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC)
```

This is implemented by `api.core.util.UtcDateTimes.now(Clock)`. Callers must
preserve constructor-injected `Clock` instances so fixed-clock tests remain
deterministic. Do not replace it with `LocalDateTime.now()` or a static system
clock.

### JDBC row conversion

`api.persistence.RowValues` is already the canonical boundary for numeric,
boolean, text, date, and timestamp values. New modules must use it rather than
adding `RowMapper`, `asString`, `toLong`, or nullable timestamp variants in a
domain package.

### Bounded list and query input

`api.shared.filter.ListFilter` owns bounded pagination and positive-ID parsing.
New list endpoints should reuse it instead of implementing local limit/offset
clamps.

## Helpers that must remain domain-owned

- `required(...)` helpers that produce domain-specific HTTP messages or enforce
  different length/range rules.
- `blank(...)`, `normalize(...)`, and `normalized(...)` helpers when they differ
  in case folding, fallback behavior, allowed characters, or field purpose.
- Webhook template rendering, warehouse overview formatting, raid-helper payload
  rendering, MIME formatting, and strategy/document serialization. These are
  business/presentation policies, not generic string utilities.
- Permission and scope checks. Do not hide fleet/member authorization in a
  generic helper.

## Current audit findings

- UTC timestamp conversion is centralized in `api.core.util.UtcDateTimes`; all
  formerly duplicated `private LocalDateTime now()` wrappers use it.
- Repeated blank-to-null implementations exist in groups, squads, onboarding,
  webhooks, fleet, and securityops, but their callers do not currently share a
  documented validation contract.
- Multiple `required`/`normalize` helpers look similar textually but have
  different labels, limits, case rules, or domain semantics. They should not be
  merged mechanically.

## Agent workflow

1. Search this guide and `api.persistence.RowValues` before creating a helper.
2. Extract only a pure function with at least two behaviorally identical callers.
3. Add a focused unit test for null, whitespace, timezone, and fixed-clock cases
   relevant to the helper.
4. Migrate callers in a bounded commit; do not leave a duplicate wrapper unless
   it is a documented compatibility boundary.
5. Run the affected module tests, strict-tree validation, and the repository gate.

The next recommended cleanup unit is a narrowly scoped text normalization
candidate, but only where callers share an identical validation contract. Keep
that work separate from the UTC extraction so regressions remain easy to
attribute.
