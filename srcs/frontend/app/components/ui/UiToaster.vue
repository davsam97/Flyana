<script setup lang="ts">
const { toasts, dismiss } = useToast()
</script>

<template>
  <!-- Always in the DOM, even empty: a live region inserted together with its
       content is often not announced by screen readers -->
  <div
    aria-live="polite"
    class="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col gap-3 sm:inset-x-auto sm:right-6 sm:bottom-6 sm:w-80"
  >
    <TransitionGroup
      enter-from-class="translate-y-2 opacity-0"
      enter-active-class="transition duration-base ease-out motion-reduce:transition-none"
      leave-active-class="transition duration-base ease-in motion-reduce:transition-none"
      leave-to-class="opacity-0"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="pointer-events-auto flex items-start gap-3 rounded-lg border border-line-subtle bg-surface-card p-4 shadow-lg"
      >
        <span v-if="toast.emoji" class="text-2xl" aria-hidden="true">{{ toast.emoji }}</span>
        <div class="flex-1 text-sm">
          <p class="font-semibold">{{ toast.title }}</p>
          <p v-if="toast.body" class="text-fg-muted">{{ toast.body }}</p>
        </div>
        <button
          type="button"
          class="rounded text-fg-subtle hover:text-fg-body focus-visible:shadow-focus focus-visible:outline-none"
          :aria-label="$t('toast.close')"
          @click="dismiss(toast.id)"
        >
          <Icon name="lucide:x" mode="svg" size="1em" aria-hidden="true" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
