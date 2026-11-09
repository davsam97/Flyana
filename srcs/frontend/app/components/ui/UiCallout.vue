<script setup lang="ts">
type Tone = 'socratic' | 'hint' | 'success' | 'info' | 'danger'

const {
  tone = 'socratic',
  icon,
  title,
} = defineProps<{
  tone?: Tone
  icon?: string
  title?: string
}>()

const STYLES: Record<Tone, string> = {
  socratic: 'bg-accent-soft',
  hint: 'bg-warning-soft',
  success: 'bg-success-soft',
  info: 'bg-accent-2-soft',
  danger: 'bg-danger-soft',
}

const ICON_COLORS: Record<Tone, string> = {
  socratic: 'text-accent',
  hint: 'text-warning',
  success: 'text-success',
  info: 'text-accent-2',
  danger: 'text-danger',
}
</script>

<template>
  <div :class="['flex gap-3 rounded-lg p-4 text-sm leading-normal', STYLES[tone]]">
    <div v-if="icon" :class="['flex h-[1lh] flex-none items-center', ICON_COLORS[tone]]">
      <Icon :name="icon" mode="svg" size="1.125em" aria-hidden="true" />
    </div>
    <div class="min-w-0 break-words">
      <div v-if="title" class="font-semibold">
        {{ title }}
      </div>
      <div class="text-fg-muted">
        <slot />
      </div>
    </div>
  </div>
</template>
