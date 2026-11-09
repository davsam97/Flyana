<script setup lang="ts">
defineProps<{
  label: string
}>()
</script>

<template>
  <button
    type="button"
    class="flex w-full items-center gap-3 rounded-md px-2 py-2.5 text-left text-sm font-semibold transition-colors duration-slow ease-out hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:shadow-focus focus-visible:outline-none"
  >
    <span v-if="$slots.default" aria-hidden="true">
      <slot />
    </span>
    {{ label }}
  </button>
</template>
