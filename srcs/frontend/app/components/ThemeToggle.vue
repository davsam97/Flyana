<script setup lang="ts">
const { variant = 'ghost' } = defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost'
}>()

const colorMode = useColorMode()

const isDark = computed(() => colorMode.value === 'dark')

function toggle() {
  colorMode.preference = isDark.value ? 'light' : 'dark'
}
</script>

<template>
  <UiButton
    :variant="variant"
    :label="isDark ? $t('theme.light') : $t('theme.dark')"
    @click="toggle"
  >
    <Icon :name="isDark ? 'lucide:sun' : 'lucide:moon'" mode="svg" size="1.25em" />
  </UiButton>
</template>
