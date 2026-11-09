<template>
  <div class="min-h-dvh w-full flex flex-col items-center pb-16 sm:pb-0">
    <slot />
    <AppFooter />
    <ThemeToggle variant="secondary" class="fixed bottom-5 left-5 z-50 shadow-md" />
  </div>
</template>
