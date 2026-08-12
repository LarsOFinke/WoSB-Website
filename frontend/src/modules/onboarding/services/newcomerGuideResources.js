import { createGuideBlock, createGuideResource } from '../domain/newcomerGuideDraft.js'

export function appendLinkedResource(blocks, resourceType, preferredBlock = null) {
  if (!Array.isArray(blocks) || !['guide', 'build'].includes(resourceType)) return null

  let block = preferredBlock?.block_type === 'resources' && blocks.includes(preferredBlock)
    ? preferredBlock
    : blocks.find((entry) => entry.block_type === 'resources')
  if (!block) {
    block = createGuideBlock('resources')
    blocks.push(block)
  }
  if (!Array.isArray(block.resources)) block.resources = []
  block.resources.push({ ...createGuideResource(), resource_type: resourceType })
  return block
}
