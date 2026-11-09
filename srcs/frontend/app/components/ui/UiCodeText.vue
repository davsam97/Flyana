<script setup lang="ts">
const { text } = defineProps<{
  text: string
}>()

const segments = computed(() =>
  text.split('`').map((value, index) => ({ value, code: index % 2 === 1 })),
)
</script>

<template>
  <template v-for="(segment, index) in segments" :key="index">
    <code
      v-if="segment.code"
      class="rounded-xs bg-surface-raised px-1 py-0.5 font-mono text-[0.9em]"
      >{{ segment.value }}</code
    >
    <template v-else>{{ segment.value }}</template>
  </template>
</template>
