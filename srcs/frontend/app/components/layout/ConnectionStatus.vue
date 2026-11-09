<script setup lang="ts">
const { status, latency } = useRealtime()

const DOT: Record<string, string> = {
  idle: 'bg-fg-subtle',
  connecting: 'bg-warning animate-pulse',
  online: 'bg-success',
  offline: 'bg-danger animate-pulse',
}
</script>

<template>
  <div class="flex items-center gap-2 px-4 py-2 text-2xs text-fg-subtle">
    <span aria-hidden="true" class="size-1.5 flex-none rounded-full" :class="DOT[status]" />
    <span>{{ $t(`realtime.${status}`) }}</span>
    <span v-if="latency !== null" class="ml-auto font-mono">{{ latency }} ms</span>
  </div>
</template>
