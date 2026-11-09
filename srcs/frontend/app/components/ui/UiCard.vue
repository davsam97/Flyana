<script setup lang="ts">
const { pad = false, interactive = false } = defineProps<{
  pad?: boolean
  interactive?: boolean
}>()
</script>

<template>
  <div
    class="rounded-lg border border-line-subtle bg-surface-card shadow-sm"
    :class="[
      pad ? 'p-5' : '',
      interactive
        ? 'cursor-pointer transition duration-base ease-out hover:-translate-y-0.5 hover:border-line-strong hover:shadow-md'
        : '',
    ]"
  >
    <slot />
  </div>
</template>
