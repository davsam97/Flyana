/* Short-lived notices; any component pushes, the layout's `UiToaster` renders */

export interface Toast {
  id: number
  title: string
  body?: string
  emoji?: string
}

const TOAST_DURATION_MS = 6000

const toasts = ref<Toast[]>([])
let nextId = 0

function dismiss(id: number) {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

function push(toast: Omit<Toast, 'id'>) {
  const id = nextId++
  toasts.value = [...toasts.value, { ...toast, id }]
  setTimeout(() => dismiss(id), TOAST_DURATION_MS)
}

export function useToast() {
  return { toasts: readonly(toasts), push, dismiss }
}
