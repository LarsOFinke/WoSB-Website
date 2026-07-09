# UI/UX Notes

## Registration

The registration view is split into two task groups:

1. Account details
2. Fleet connection

Fields now have stronger background contrast, persistent labels, helper text and visible focus states. Fleet selection also shows a selected-fleet preview and an optional application note for fleet leadership.

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

Labels should stay visible outside inputs. Place hints below the input instead of relying on placeholders alone.

## Filters

Filters should appear as a dedicated task area above lists. Prefer a short heading, one row of controls and predictable responsive stacking.

## Color and contrast

The dark theme uses a navy/slate base and warm gold accents. New components should use existing CSS tokens and avoid introducing one-off colors unless they are promoted into `:root` tokens.
