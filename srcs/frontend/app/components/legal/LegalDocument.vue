<script setup lang="ts">
/* Sections come straight from the locale file (`legal.<doc>.sections`), in
   file order, so adding one is a translation change only. */
const { doc } = defineProps<{
  doc: 'privacy' | 'terms'
}>()

const { tm } = useI18n()
const router = useRouter()

const sections = computed(() => Object.keys(tm(`legal.${doc}.sections`) as object))

function back() {
  if (window.history.length > 1) router.back()
  else navigateTo('/')
}
</script>

<template>
  <div class="flex w-full flex-1 flex-col">
    <AppHeader />
    <main class="mx-auto w-full max-w-180 flex-1 px-4 pt-4 pb-10 sm:px-8">
      <UiButton variant="ghost" size="sm" :label="$t('legal.back')" class="mb-4" @click="back">
        <Icon name="lucide:arrow-left" mode="svg" size="1em" />
      </UiButton>
      <h1 class="mb-1 text-2xl tracking-tight sm:text-3xl">{{ $t(`legal.${doc}.title`) }}</h1>
      <p class="mb-6 text-sm text-fg-subtle">{{ $t('legal.updated') }}</p>
      <p class="mb-8 text-md leading-relaxed text-fg-muted">{{ $t(`legal.${doc}.intro`) }}</p>
      <section v-for="(key, index) in sections" :key="key" class="mb-7">
        <h2 class="mb-2 text-lg font-semibold sm:text-xl">
          {{ index + 1 }}. {{ $t(`legal.${doc}.sections.${key}.title`) }}
        </h2>
        <p class="text-md leading-relaxed whitespace-pre-line text-fg-muted">
          {{ $t(`legal.${doc}.sections.${key}.body`) }}
        </p>
      </section>
    </main>
  </div>
</template>
