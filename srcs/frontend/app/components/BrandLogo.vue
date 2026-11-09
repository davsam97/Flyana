<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

const { to = '/dashboard' } = defineProps<{
  to?: RouteLocationRaw
}>()
</script>

<template>
  <NuxtLink
    :to="to"
    class="flex items-center gap-3 rounded-md text-xl leading-relaxed font-semibold text-fg-body focus-visible:shadow-focus focus-visible:outline-none"
  >
    <div aria-hidden="true" class="h-fit w-fit rounded-md bg-accent p-2 text-on-accent">
      <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
        <!-- A heavy launcher leaving the equator: a core stage between two
             strap-on boosters, the way they rise from the Guianese coast -->
        <path
          fill="currentColor"
          d="M12 .8c1.7 1.5 2.3 3.2 2.3 4.9V19H9.7V5.7c0-1.7.6-3.4 2.3-4.9ZM8.1 8.6c.9.8 1.25 1.6 1.25 2.5v7.4H6.85v-7.4c0-.9.35-1.7 1.25-2.5Zm7.8 0c.9.8 1.25 1.6 1.25 2.5v7.4h-2.5v-7.4c0-.9.35-1.7 1.25-2.5Z"
        />
        <path
          class="fill-accent-3"
          d="M10.2 19.6h3.6L12 23.4ZM7 19.1h2.2L8.1 21.9Zm7.8 0H17l-1.1 2.8Z"
        />
      </svg>
    </div>
    Flyana
  </NuxtLink>
</template>
