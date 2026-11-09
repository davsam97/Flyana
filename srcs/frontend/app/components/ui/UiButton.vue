<script setup lang="ts">
type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

const {
  label,
  variant = 'primary',
  size = 'md',
  type = 'button',
  block = false,
  to,
} = defineProps<{
  label: string
  variant?: Variant
  size?: Size
  type?: 'button' | 'submit' | 'reset'
  block?: boolean
  to?: string
}>()

const NuxtLink = resolveComponent('NuxtLink')
const tag = computed(() => (to ? NuxtLink : 'button'))
const tagAttrs = computed(() => (to ? { to } : { type }))

const BASE =
  'inline-flex items-center justify-center gap-2 rounded-md border leading-none font-semibold whitespace-nowrap transition-colors duration-fast focus-visible:outline-none focus-visible:shadow-focus disabled:pointer-events-none disabled:opacity-50'

const VARIANTS: Record<Variant, string> = {
  primary: 'border-transparent bg-accent text-on-accent hover:bg-accent-hover',
  secondary: 'border-line-strong bg-surface-raised text-fg-body hover:bg-surface-hover',
  ghost: 'border-transparent text-fg-muted hover:bg-surface-hover hover:text-fg-body',
  danger: 'border-transparent bg-danger text-white hover:opacity-90',
}

const SIZES: Record<Size, string> = {
  sm: 'h-6 px-3 text-sm',
  md: 'h-7 px-4 text-sm',
  lg: 'h-8 px-5 text-md',
}
</script>

<template>
  <component
    :is="tag"
    v-bind="tagAttrs"
    :class="[BASE, VARIANTS[variant], SIZES[size], block ? 'w-full' : '']"
  >
    <span v-if="$slots.default" aria-hidden="true">
      <slot />
    </span>
    <span>{{ label }}</span>
    <span v-if="$slots.trailing" aria-hidden="true">
      <slot name="trailing" />
    </span>
  </component>
</template>
