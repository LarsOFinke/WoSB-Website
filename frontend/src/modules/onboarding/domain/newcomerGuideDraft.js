export function createGuideBlock(blockType = 'text') {
  return { block_type: blockType, title: '', body: '', resources: [] }
}

export function createGuideResource() {
  return { resource_type: 'guide', resource_id: null, label: '', description: '', url: '' }
}

export function createGuideDraft(source) {
  return {
    title: source.title,
    intro: source.intro,
    blocks: (source.blocks || []).map((block) => ({
      block_type: block.block_type,
      title: block.title,
      body: block.body || '',
      resources: (block.resources || []).map((resource) => ({
        resource_type: resource.resource_type,
        resource_id: resource.resource_id || null,
        label: resource.label || '',
        description: resource.description || '',
        url: ['internal', 'external'].includes(resource.resource_type) ? resource.href : '',
      })),
    })),
  }
}

export function guidePayload(draft) {
  return {
    title: draft.title,
    intro: draft.intro,
    blocks: draft.blocks.map((block) => ({
      block_type: block.block_type,
      title: block.title,
      body: block.body || null,
      resources: block.block_type === 'resources'
        ? block.resources.map((resource) => ({
            resource_type: resource.resource_type,
            resource_id: ['guide', 'build'].includes(resource.resource_type) ? Number(resource.resource_id) : null,
            label: resource.label || null,
            description: resource.description || null,
            url: ['internal', 'external'].includes(resource.resource_type) ? resource.url : null,
          }))
        : [],
    })),
  }
}

export function moveArrayItem(items, index, delta) {
  const target = index + delta
  if (target < 0 || target >= items.length) return false
  const [item] = items.splice(index, 1)
  items.splice(target, 0, item)
  return true
}

export function resetGuideResource(resource) {
  resource.resource_id = null
  resource.url = ''
}

export function resourceComponent(resource) {
  return resource.resource_type === 'external' ? 'a' : 'RouterLink'
}

export function resourceTarget(resource) {
  return resource.resource_type === 'external'
    ? { href: resource.href, target: '_blank', rel: 'noopener' }
    : { to: resource.href }
}
