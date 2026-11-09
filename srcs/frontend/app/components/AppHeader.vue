<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

const { to = '/' } = defineProps<{
  to?: RouteLocationRaw
}>()
</script>

<template>
  <header
    class="flex w-full flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-8 sm:py-5"
  >
    <BrandLogo :to="to" />
    <div class="ml-auto flex items-center gap-2 sm:gap-3">
      <LanguageSwitcher />
      <slot />
    </div>
  </header>
</template>
