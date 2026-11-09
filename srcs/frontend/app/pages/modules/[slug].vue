<script setup lang="ts">
import type { ModuleDetail } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const route = useRoute()
const { t, locale } = useI18n()
const course = useCourse()

const module = ref<ModuleDetail | null>(null)
const failed = ref(false)
const starting = ref(false)

const slug = computed(() => String(route.params.slug))

async function load() {
  failed.value = false
  try {
    module.value = await course.module(slug.value)
  } catch {
    failed.value = true
  }
}

async function startQuiz() {
  starting.value = true
  try {
    const run = await course.startQuiz(slug.value)
    await navigateTo(`/quiz/${run.id}`)
  } catch {
    failed.value = true
  } finally {
    starting.value = false
  }
}

const firstUnread = computed(() => module.value?.lessons.find((lesson) => !lesson.read) ?? null)

const breadcrumb = computed(() => [
  { label: t('nav.course'), to: '/parcours' },
  { label: module.value?.name ?? '' },
])

onMounted(load)
watch([locale, slug], load)
</script>

<template>
  <div class="mx-auto w-full max-w-200">
    <p v-if="failed" class="text-danger">{{ $t('course.loadFailed') }}</p>
    <template v-else-if="module">
      <UiBreadcrumb :items="breadcrumb" :label="$t('course.breadcrumb')" class="mb-4" />
      <header class="mb-6 flex items-start gap-4">
        <span
          aria-hidden="true"
          class="flex size-14 flex-none items-center justify-center rounded-lg bg-accent-soft text-accent"
        >
          <Icon :name="moduleIcon(module.slug)" mode="svg" size="1.75em" />
        </span>
        <div>
          <p class="font-mono text-xs text-fg-subtle">
            {{ $t('course.moduleNumber', { n: module.position + 1 }) }}
          </p>
          <h1 class="text-2xl sm:text-3xl">{{ module.name }}</h1>
          <p v-if="module.description" class="mt-1 text-fg-muted">{{ module.description }}</p>
        </div>
      </header>

      <section class="mb-6">
        <div class="mb-3 flex items-baseline justify-between gap-3">
          <h2 class="text-xl font-semibold">{{ $t('course.lessons') }}</h2>
          <span class="text-xs text-fg-subtle">{{
            $t('course.lessonsRead', { n: module.lessons_read, total: module.lessons_total })
          }}</span>
        </div>
        <p v-if="!module.lessons.length" class="text-fg-muted">{{ $t('course.noLessons') }}</p>
        <ol v-else class="flex flex-col gap-2">
          <li v-for="(lesson, index) in module.lessons" :key="lesson.slug">
            <NuxtLink
              :to="`/lecons/${lesson.slug}`"
              class="flex items-center gap-3 rounded-md border border-line-subtle px-4 py-3 hover:bg-surface-hover focus-visible:shadow-focus focus-visible:outline-none"
            >
              <span
                class="flex size-7 flex-none items-center justify-center rounded-md font-mono text-sm"
                :class="
                  lesson.read ? 'bg-success-soft text-success' : 'bg-surface-raised text-fg-muted'
                "
              >
                <Icon
                  v-if="lesson.read"
                  name="lucide:check"
                  mode="svg"
                  :aria-label="$t('course.read')"
                />
                <template v-else>{{ index + 1 }}</template>
              </span>
              <span class="flex-1">{{ lesson.title }}</span>
              <Icon
                name="lucide:chevron-right"
                mode="svg"
                aria-hidden="true"
                class="text-fg-subtle"
              />
            </NuxtLink>
          </li>
        </ol>
        <UiButton
          v-if="firstUnread"
          :label="module.lessons_read ? $t('course.continueReading') : $t('course.startReading')"
          :to="`/lecons/${firstUnread.slug}`"
          variant="secondary"
          class="mt-3"
        />
      </section>

      <UiCard pad class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-xl font-semibold">{{ $t('course.quizTitle') }}</h2>
          <UiTag v-if="module.passed" type="success" :label="$t('course.passed')" />
        </div>
        <p class="text-sm text-fg-muted">
          {{ $t('course.quizBody', { n: module.quiz_questions }) }}
        </p>
        <p v-if="module.best_score !== null" class="text-sm">
          {{ $t('course.bestScore', { n: percent(module.best_score) }) }}
          · {{ $t('course.quizzes', module.quizzes) }}
        </p>
        <p v-if="!module.quiz_questions" class="text-sm text-fg-subtle">
          {{ $t('course.noQuestions') }}
        </p>
        <div v-else class="flex flex-wrap gap-3">
          <UiButton
            v-if="module.open_run_id"
            :label="$t('course.resumeQuiz')"
            :to="`/quiz/${module.open_run_id}`"
          />
          <UiButton
            :label="module.open_run_id ? $t('course.restartQuiz') : $t('course.startQuiz')"
            :variant="module.open_run_id ? 'secondary' : 'primary'"
            :disabled="starting"
            @click="startQuiz"
          />
        </div>
      </UiCard>
    </template>
  </div>
</template>
