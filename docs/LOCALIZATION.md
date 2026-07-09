# Localization Notes

The frontend ships with seven supported locales:

- `de` German
- `en` English, canonical source language
- `fr` French
- `es` Spanish
- `pt` Portuguese
- `ru` Russian
- `cn` Simplified Chinese (`zh-CN` HTML language)

## Runtime structure

Localization lives under `frontend/src/locales/`:

```text
config.js                    supported locale metadata
index.js                     small runtime API used by Vue components
utils.js                     nested key lookup, merge and message formatting helpers
glossaries/optionTerms.js    catalog/option term glossaries
messages/*.js                feature-oriented message layers
autoLocalization.js          final coverage pass for non-English feature layers
```

`messages/index.js` composes all feature layers, merges English as the canonical baseline and then runs a final locale fill pass. A final `localeCompletenessMessages` layer is applied afterwards for strings that must never be auto-generated, such as dynamic labels, build stat labels and forum category aliases.

## Validation

Run this after adding, renaming or moving keys:

```bash
npm run check:locales
```

The check verifies four things:

1. every supported locale exposes the same key set
2. non-English locales do not accidentally display unapproved English fallback strings
3. no auto-generated pseudo labels such as `FR · ...` remain visible
4. known dynamic key contracts, such as forum categories, guide categories, group statuses and focus labels, are present

A successful run should look like this:

```text
en: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
de: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
fr: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
es: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
pt: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
ru: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
cn: 937 keys, missing 0, english-fallback 0, pseudo 0, dynamic-missing 0
```

Some domain terms intentionally remain unchanged across languages, for example `Forum`, `Guides`, `PvE`, `PvP`, file-format labels and other community/game terms. These are explicitly allowlisted in `scripts/check-locales.mjs` so real accidental fallback strings still fail the check.

## Dynamic keys and aliases

Some labels are constructed from backend values, for example `forum.categories.${thread.category}`. These values are covered by the locale contract check. Forum categories currently include `general`, `builds`, `events`, `support`, `training` and `logistics`. The legacy typo alias `loistics` is also localized and normalized to `logistics` so older local databases do not display raw keys.

## Component rule

Vue components should never hard-code visible UI text. Use `t('path.to.key')` for:

- labels
- placeholders
- button text
- empty states
- errors
- aria labels
- navigation group names

Keep placeholders as hints, not as the only label. Persistent labels and helper text are part of the current form style.
