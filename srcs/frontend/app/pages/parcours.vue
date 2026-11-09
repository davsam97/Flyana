<script setup lang="ts">
import type { LearningPath } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { path } = useCourse()
const { locale } = useI18n()

const course = ref<LearningPath | null>(null)
const failed = ref(false)

async function load() {
  failed.value = false
  try {
    course.value = await path()
  } catch {
    failed.value = true
  }
}

const passedCount = computed(() => course.value?.modules.filter((m) => m.passed).length ?? 0)

onMounted(load)
watch(locale, load)
</script>

<template>
  <div class="mx-auto w-full max-w-260">
    <p v-if="failed" class="text-danger">{{ $t('course.loadFailed') }}</p>
    <template v-else-if="course">
      <header class="mb-6">
        <p class="text-sm text-fg-subtle">{{ $t('nav.course') }}</p>
        <h1 class="text-2xl sm:text-3xl">{{ course.title }}</h1>
        <p v-if="course.description" class="mt-1.5 max-w-150 text-fg-muted">
          {{ course.description }}
        </p>
        <div class="mt-4 flex max-w-110 flex-col gap-1.5">
          <p class="text-xs text-fg-subtle">
            {{ $t('course.modulesPassed', { n: passedCount, total: course.modules.length }) }}
          </p>
          <UiProgress
            :value="passedCount"
            :max="Math.max(1, course.modules.length)"
            tone="success"
          />
        </div>
      </header>

      <ol class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <li v-for="module in course.modules" :key="module.slug">
          <CourseModuleCard :module="module" />
        </li>
      </ol>
    </template>
  </div>
</template>
