const DEFAULT_MARGIN = 16
const DEFAULT_GAP = 6
const DEFAULT_MIN_WIDTH = 384
const DEFAULT_MAX_WIDTH = 544
const DEFAULT_MAX_HEIGHT = 384
const FLIP_THRESHOLD = 240

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum)
}

export function calculatePickerPlacement(rect, viewport, options = {}) {
  const margin = options.margin ?? DEFAULT_MARGIN
  const gap = options.gap ?? DEFAULT_GAP
  const minWidth = options.minWidth ?? DEFAULT_MIN_WIDTH
  const maxWidth = options.maxWidth ?? DEFAULT_MAX_WIDTH
  const maxHeight = options.maxHeight ?? DEFAULT_MAX_HEIGHT

  const viewportWidth = Math.max(0, Number(viewport?.width || 0))
  const viewportHeight = Math.max(0, Number(viewport?.height || 0))
  const availableWidth = Math.max(0, viewportWidth - (margin * 2))
  const width = Math.min(Math.max(Number(rect?.width || 0), minWidth), maxWidth, availableWidth)
  const left = clamp(Number(rect?.left || 0), margin, Math.max(margin, viewportWidth - width - margin))
  const spaceBelow = Math.max(0, viewportHeight - Number(rect?.bottom || 0) - gap - margin)
  const spaceAbove = Math.max(0, Number(rect?.top || 0) - gap - margin)
  const placement = spaceBelow < FLIP_THRESHOLD && spaceAbove > spaceBelow ? 'top' : 'bottom'
  const availableHeight = placement === 'top' ? spaceAbove : spaceBelow
  const maxMenuHeight = Math.min(maxHeight, availableHeight)

  return {
    placement,
    left,
    width,
    maxHeight: maxMenuHeight,
    top: placement === 'bottom' ? Number(rect?.bottom || 0) + gap : null,
    bottom: placement === 'top' ? viewportHeight - Number(rect?.top || 0) + gap : null,
  }
}
