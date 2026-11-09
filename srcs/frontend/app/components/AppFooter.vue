<script setup lang="ts">
const LINK =
  'rounded-sm text-fg-muted transition-colors duration-fast hover:text-fg-body focus-visible:shadow-focus focus-visible:outline-none'
</script>

<template>
  <footer
    class="flex w-full flex-wrap items-center justify-center gap-x-5 gap-y-1 px-4 py-5 text-center sm:px-8 text-xs text-fg-subtle"
  >
    <span>© {{ new Date().getFullYear() }} Flyana · {{ $t('legal.footer.project') }}</span>
    <nav class="flex gap-5" :aria-label="$t('legal.footer.terms')">
      <NuxtLink to="/privacy" :class="LINK">{{ $t('legal.footer.privacy') }}</NuxtLink>
      <NuxtLink to="/terms" :class="LINK">{{ $t('legal.footer.terms') }}</NuxtLink>
    </nav>
  </footer>
</template>
