<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

const { items, label } = defineProps<{
  items: { label: string; to?: RouteLocationRaw }[]
  label: string
}>()
</script>

<template>
  <nav :aria-label="label">
    <ol class="flex flex-wrap items-center gap-1.5 text-sm text-fg-muted">
      <li v-for="(item, index) in items" :key="index" class="flex items-center gap-1.5">
        <Icon
          v-if="index > 0"
          name="lucide:chevron-right"
          mode="svg"
          size="0.875em"
          aria-hidden="true"
          class="text-fg-subtle"
        />
        <NuxtLink
          v-if="item.to"
          :to="item.to"
          class="rounded-xs hover:text-fg-body focus-visible:shadow-focus focus-visible:outline-none"
        >
          {{ item.label }}
        </NuxtLink>
        <span v-else aria-current="page" class="font-semibold text-fg-body">{{ item.label }}</span>
      </li>
    </ol>
  </nav>
</template>
