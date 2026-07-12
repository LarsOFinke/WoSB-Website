export function appendLinkedResource(blocks, resourceType) {
  if (!Array.isArray(blocks) || !['guide', 'build'].includes(resourceType)) return null

  let block = blocks.find((entry) => entry.block_type === 'resources')
  if (!block) {
    block = { block_type: 'resources', title: '', body: '', resources: [] }
    blocks.push(block)
  }
  if (!Array.isArray(block.resources)) block.resources = []
  block.resources.push({
    resource_type: resourceType,
    resource_id: null,
    label: '',
    description: '',
    url: '',
  })
  return block
}
