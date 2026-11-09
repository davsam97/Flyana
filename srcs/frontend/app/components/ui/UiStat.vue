<script setup lang="ts">
const { value, label } = defineProps<{
  value: string | number
  label: string
}>()
</script>

<template>
  <div class="flex flex-col gap-0.5">
    <span class="text-2xl font-semibold">{{ value }}</span>
    <span class="text-xs text-fg-subtle">{{ label }}</span>
  </div>
</template>
