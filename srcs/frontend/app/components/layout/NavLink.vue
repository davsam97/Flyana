<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

const { badge = 0, activePrefix } = defineProps<{
  label: string
  to: RouteLocationRaw
  badge?: number
  // Paths below the link's own that still light it up
  activePrefix?: string | string[]
}>()

const ACTIVE = 'bg-accent-soft text-accent-press'

const route = useRoute()
const inSection = computed(() =>
  [activePrefix ?? []].flat().some((prefix) => route.path.startsWith(prefix)),
)
</script>

<template>
  <NuxtLink
    :to="to"
    class="flex items-center gap-3 rounded-md px-2 py-2.5 text-sm font-semibold transition-colors duration-slow ease-out hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:shadow-focus focus-visible:outline-none"
    :class="inSection ? ACTIVE : ''"
    :active-class="ACTIVE"
  >
    <span v-if="$slots.default" aria-hidden="true">
      <slot />
    </span>
    <span class="flex-1">{{ label }}</span>
    <span
      v-if="badge > 0"
      class="flex-none rounded-full bg-accent px-1.5 text-xs font-semibold text-on-accent"
    >
      {{ badge > 99 ? '99+' : badge }}
    </span>
  </NuxtLink>
</template>
