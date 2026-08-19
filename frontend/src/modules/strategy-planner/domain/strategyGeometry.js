export function strategyObjectScale(object) {
  const value = Number(object?.scale ?? 1)
  return Number.isFinite(value) ? Math.max(0.25, Math.min(4, value)) : 1
}

export function strategyLineGeometry(object, canvasHeight, canvasWidth = 1000) {
  const x1 = Number(object.x) * canvasWidth
  const y1 = Number(object.y) * canvasHeight
  const x2 = Number(object.x2) * canvasWidth
  const y2 = Number(object.y2) * canvasHeight
  const centerX = (x1 + x2) / 2
  const centerY = (y1 + y2) / 2
  const scale = strategyObjectScale(object)
  const startX = centerX + (x1 - centerX) * scale
  const startY = centerY + (y1 - centerY) * scale
  const endX = centerX + (x2 - centerX) * scale
  const endY = centerY + (y2 - centerY) * scale
  return {
    x1: startX,
    y1: startY,
    x2: endX,
    y2: endY,
    centerX,
    centerY,
    angle: Math.atan2(endY - startY, endX - startX) * 180 / Math.PI,
  }
}

export function strategyFormationPath(object, canvasHeight, canvasWidth = 1000) {
  let width = Number(object.width || 0.32) * canvasWidth * strategyObjectScale(object)
  let height = Number(object.height || 0.24) * canvasHeight * strategyObjectScale(object)
  if (object.formation === 'circle') width = height = Math.min(width, height)
  if (object.formation === 'circle' || object.formation === 'oval') {
    return `M ${-width / 2} 0 A ${width / 2} ${height / 2} 0 1 0 ${width / 2} 0 A ${width / 2} ${height / 2} 0 1 0 ${-width / 2} 0`
  }
  if (object.formation === 'wedge') return `M ${-width / 2} ${height / 2} L 0 ${-height / 2} L ${width / 2} ${height / 2}`
  if (object.formation === 'column') return `M 0 ${-height / 2} L 0 ${height / 2}`
  if (object.formation === 'box') return `M ${-width / 2} ${-height / 2} H ${width / 2} V ${height / 2} H ${-width / 2} Z`
  return `M ${-width / 2} 0 L ${width / 2} 0`
}
