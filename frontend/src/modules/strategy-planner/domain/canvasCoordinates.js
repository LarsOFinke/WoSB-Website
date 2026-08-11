function clamp(value) {
  return Math.max(0, Math.min(1, value))
}

export function strategyCanvasPoint(svg, event, canvasHeight) {
  const height = Number(canvasHeight)
  if (!svg || !Number.isFinite(height) || height <= 0) return { x: 0, y: 0 }
  try {
    const matrix = svg.getScreenCTM?.()
    if (matrix && typeof matrix.inverse === 'function' && typeof svg.createSVGPoint === 'function') {
      const screenPoint = svg.createSVGPoint()
      screenPoint.x = event.clientX
      screenPoint.y = event.clientY
      const canvasPoint = screenPoint.matrixTransform(matrix.inverse())
      return { x: clamp(canvasPoint.x / 1000), y: clamp(canvasPoint.y / height) }
    }
  } catch {
    // A detached or temporarily hidden SVG can have a non-invertible screen matrix.
  }
  const bounds = svg.getBoundingClientRect()
  return {
    x: clamp((event.clientX - bounds.left) / bounds.width),
    y: clamp((event.clientY - bounds.top) / bounds.height),
  }
}
