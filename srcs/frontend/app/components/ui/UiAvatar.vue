<script setup lang="ts">
const {
  name,
  src = null,
  size = 40,
  ring = false,
} = defineProps<{
  name: string
  src?: string | null
  size?: number
  ring?: boolean
}>()

const initials = computed(() => {
  const letters = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0] ?? '')
    .join('')
  return letters.toUpperCase() || '·'
})

const broken = ref(false)
watch(
  () => src,
  () => (broken.value = false),
)
</script>

<template>
  <img
    v-if="src"
    :src="src"
    :alt="name"
    class="inline-flex flex-none rounded-full object-cover"
    :class="ring ? 'shadow-avatar-ring' : 'shadow-ring-inset'"
    :style="{ width: `${size}px`, height: `${size}px` }"
  />
  <span
    v-else
    aria-hidden="true"
    class="inline-flex flex-none items-center justify-center overflow-hidden rounded-full bg-accent-soft font-semibold text-accent"
    :class="ring ? 'shadow-avatar-ring' : 'shadow-ring-inset'"
    :style="{ width: `${size}px`, height: `${size}px`, fontSize: `${size * 0.4}px` }"
  >
    <img
      v-if="src && !broken"
      :src="src"
      alt=""
      class="h-full w-full object-cover"
      @error="broken = true"
    />
    <template v-else>{{ initials }}</template>
  </span>
</template>
