<script setup lang="ts">
const model = defineModel<string>()

const BASE =
  'min-h-24 w-full resize-y rounded-md border border-line-strong bg-surface-raised px-3 py-2.5 font-mono text-sm leading-relaxed text-fg-body transition-[border-color,box-shadow] duration-fast placeholder:text-fg-subtle focus-visible:border-accent-2 focus-visible:shadow-focus focus-visible:outline-none'
</script>

<template>
  <textarea v-model="model" :class="BASE" />
</template>
