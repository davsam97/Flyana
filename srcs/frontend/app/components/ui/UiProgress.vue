<script setup lang="ts">
type Tone = 'accent' | 'xp' | 'success'
type Size = 'md' | 'lg'

const {
  value,
  max = 100,
  tone = 'accent',
  size = 'md',
} = defineProps<{
  value: number
  max?: number
  tone?: Tone
  size?: Size
}>()

const percentage = computed(() => Math.min(100, Math.max(0, (value / max) * 100)))

const FILLS: Record<Tone, string> = {
  accent: 'bg-accent',
  xp: 'bg-accent-3',
  success: 'bg-success',
}

const SIZES: Record<Size, string> = {
  md: 'h-2',
  lg: 'h-3',
}
</script>

<template>
  <div
    role="progressbar"
    :aria-valuenow="value"
    aria-valuemin="0"
    :aria-valuemax="max"
    class="w-full overflow-hidden rounded-full bg-surface-hover shadow-ring-inset"
    :class="SIZES[size]"
  >
    <span
      class="block h-full rounded-full transition-[width] duration-slow ease-out"
      :class="FILLS[tone]"
      :style="{ width: `${percentage}%` }"
    />
  </div>
</template>
