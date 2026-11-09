<script setup lang="ts">
const { userId, label = false } = defineProps<{
  userId: number
  label?: boolean
}>()

const { isOnline } = usePresence()
const online = computed(() => isOnline(userId))
</script>

<template>
  <span class="inline-flex items-center gap-1.5">
    <span
      aria-hidden="true"
      class="size-2 flex-none rounded-full"
      :class="online ? 'bg-success' : 'bg-line-strong'"
    />
    <span v-if="label" class="text-xs text-fg-subtle">
      {{ $t(online ? 'presence.online' : 'presence.offline') }}
    </span>
  </span>
</template>
