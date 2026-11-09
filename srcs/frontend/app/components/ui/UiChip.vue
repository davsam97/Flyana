<script setup lang="ts">
type State = 'inactive' | 'active'

const { label, active = false } = defineProps<{
  label: string
  active?: boolean
}>()

const STYLES: Record<State, string> = {
  inactive:
    'bg-surface-raised text-fg-muted border-line-subtle hover:bg-surface-hover hover:text-fg-body',
  active: 'bg-accent-soft text-accent border-transparent',
}

const state = computed(() => (active ? 'active' : 'inactive'))
</script>

<template>
  <button
    type="button"
    :aria-pressed="active"
    class="inline-flex items-center gap-1.5 rounded-sm border px-2 py-[3px] font-mono text-xs leading-snug transition-colors duration-fast focus-visible:shadow-focus focus-visible:outline-none"
    :class="STYLES[state]"
  >
    {{ label }}
  </button>
</template>
