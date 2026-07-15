import { onScopeDispose, watch } from 'vue'

/**
 * Watches reactive sources and delays the callback until changes settle.
 * The timer is scoped to the owning component/composable and is always cleaned up.
 */
export function useDebouncedWatch(source, callback, delay = 200, options) {
  let timer = null

  const stop = watch(source, (...args) => {
    globalThis.clearTimeout(timer)
    timer = globalThis.setTimeout(() => callback(...args), delay)
  }, options)

  onScopeDispose(() => {
    globalThis.clearTimeout(timer)
    stop()
  })

  return stop
}
