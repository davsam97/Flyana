<script setup lang="ts">
defineProps<{
  title: string
  subtitle: string
  altLabel?: string
  altTo?: string
}>()
</script>

<template>
  <div class="flex w-full flex-1 flex-col">
    <AppHeader>
      <NuxtLink v-if="altLabel && altTo" :to="altTo">
        <UiButton variant="ghost" :label="altLabel" />
      </NuxtLink>
    </AppHeader>

    <main class="relative flex flex-1 items-center justify-center px-4 pt-5 pb-40 sm:p-6 sm:pb-56">
      <!-- The coast at dawn along the bottom of the page, behind the form -->
      <div class="pointer-events-none absolute inset-x-0 bottom-0 h-40 opacity-90 sm:h-72">
        <GuianaScene />
      </div>
      <UiCard class="relative w-full max-w-105 p-5 sm:p-[36px]">
        <div class="mb-6 text-center">
          <h1 class="text-2xl">{{ title }}</h1>
          <p class="text-sm text-fg-muted">{{ subtitle }}</p>
        </div>
        <slot />
      </UiCard>
    </main>
  </div>
</template>
