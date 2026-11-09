<script setup lang="ts">
type TagType = 'default' | 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'streak'

const {
  type = 'default',
  label,
  dot = false,
} = defineProps<{
  type?: TagType
  label?: string
  dot?: boolean
}>()

const STYLES: Record<TagType, string> = {
  default: 'bg-default-soft text-default',
  neutral: 'border-line-subtle bg-surface-raised text-fg-muted',
  info: 'bg-accent-2-soft text-accent-2',
  success: 'bg-success-soft text-success',
  warning: 'bg-warning-soft text-warning',
  danger: 'bg-danger-soft text-danger',
  streak: 'bg-accent-3-soft text-accent-3',
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full border border-transparent px-2 py-1 text-2xs leading-none font-semibold tracking-wide"
    :class="STYLES[type]"
  >
    <span v-if="dot" aria-hidden="true" class="size-1.5 rounded-full bg-current" />
    {{ label ?? type }}
  </span>
</template>
