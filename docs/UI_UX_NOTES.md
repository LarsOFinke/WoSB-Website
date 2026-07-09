# UI/UX Notes

The frontend uses a single dark, enterprise-style design system in `frontend/src/styles/main.css`. The current UI pass focuses on strong hierarchy, predictable spacing, accessible form affordances and responsive behavior across desktop, tablet and mobile.

## Design principles

- Keep primary actions visually distinct, but do not introduce extra accent colors for every feature.
- Use persistent labels above or next to form fields. Placeholder text is only a hint, never the label.
- Group related controls in panels so users can quickly understand the task area.
- Use the shared card, filter, tab and form classes before adding local one-off styles.
- Keep list/detail surfaces calm: high contrast text, subtle borders and limited elevation.

## Registration

The registration view is split into two task groups:

1. Account details
2. Fleet connection

Fields use stronger background contrast, persistent labels, helper text and visible focus states. Fleet selection shows a selected-fleet preview and an optional application note for fleet leadership.

## Form style

Use the shared classes for new forms:

```text
auth-form
sectioned-form
form-section-card
input-panel
elevated-input-panel
form-button
primary-action
```

Every control should have a visible label. Hints belong below the field. For dark surfaces, inputs should use the elevated field treatment so they remain clearly distinguishable from the surrounding panel.

## Filters

Filters appear as a dedicated task area above lists. Prefer a short heading, one row of controls on desktop and predictable one-column stacking on mobile. Search fields, selects and actions should share the same control height and focus treatment.

## Responsive behavior

The stylesheet now defines an explicit mobile-query layer:

- `1280px`: navigation splits into multiple rows; detail/calendar layouts collapse to one column
- `1024px`: hero sections, auth/register and large management grids stack
- `768px`: navigation groups become horizontally scrollable touch rows; filters and action rows stack
- `560px`: tighter page padding, full-width actions and compact cards
- `420px`: extra-small phone refinements for brand, chips and calendar cells

Touch devices receive at least 44px interactive targets, and hover transforms are disabled for coarse pointers. The calendar remains a seven-column month grid on mobile, but event chips are reduced so the selected-day agenda carries the details.

## Color and contrast

The dark theme uses a navy/slate base and warm gold accents. New components should use existing CSS tokens and avoid introducing one-off colors unless they are promoted into `:root` tokens. Text and important component boundaries should remain visibly distinct from background surfaces.

## Motion

Transitions are intentionally subtle. `prefers-reduced-motion: reduce` disables meaningful motion so the UI remains comfortable and predictable.
