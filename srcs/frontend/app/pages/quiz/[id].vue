<script setup lang="ts">
import type { QuizAnswerBody } from '~/components/quiz/QuizQuestion.vue'
import type { Correction, QuizQuestion, QuizRun, RunResult } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const route = useRoute()
const { t } = useI18n()
const course = useCourse()
const { announce } = useAchievements()

const run = ref<QuizRun | null>(null)
const question = ref<QuizQuestion | null>(null)
const correction = ref<Correction | null>(null)
const correct = ref<boolean | null>(null)
const upcoming = ref<QuizQuestion | null>(null)
const result = ref<RunResult | null>(null)
const pendingResult = ref<RunResult | null>(null)
const answered = ref(0)
const xp = ref(0)
const busy = ref(false)
const failed = ref(false)

const id = computed(() => Number(route.params.id))

async function load() {
  failed.value = false
  try {
    const state = await course.run(id.value)
    run.value = state
    question.value = state.question
    result.value = state.result
    answered.value = state.answered
    correction.value = null
  } catch {
    failed.value = true
  }
}

async function submit(body: QuizAnswerBody) {
  if (!question.value || !run.value) return
  busy.value = true
  try {
    const outcome = await course.answer(run.value.id, { question_id: question.value.id, ...body })
    correction.value = outcome.correction
    correct.value = outcome.correct
    upcoming.value = outcome.next_question
    pendingResult.value = outcome.result
    answered.value = outcome.answered
    xp.value += outcome.xp
    announce(outcome.achievements)
  } catch {
    failed.value = true
  } finally {
    busy.value = false
  }
}

function next() {
  correction.value = null
  correct.value = null
  question.value = upcoming.value
  result.value = pendingResult.value
}

async function retry() {
  if (!run.value) return
  const fresh = await course.startQuiz(run.value.module_slug)
  xp.value = 0
  await navigateTo(`/quiz/${fresh.id}`)
}

const breadcrumb = computed(() => [
  { label: t('nav.course'), to: '/parcours' },
  ...(run.value ? [{ label: t('course.quizTitle'), to: `/modules/${run.value.module_slug}` }] : []),
])

onMounted(load)
watch(id, load)
</script>

<template>
  <div class="mx-auto w-full max-w-190">
    <p v-if="failed" class="text-danger">{{ $t('course.loadFailed') }}</p>
    <template v-else-if="run">
      <UiBreadcrumb :items="breadcrumb" :label="$t('course.breadcrumb')" class="mb-4" />

      <QuizResult
        v-if="result && !correction"
        :result="result"
        :module-slug="run.module_slug"
        :xp="xp"
        @retry="retry"
      />

      <template v-else-if="question">
        <div class="mb-5 flex flex-col gap-1.5">
          <p class="text-xs text-fg-subtle">
            {{
              $t('quiz.progress', {
                n: Math.min(answered + (correction ? 0 : 1), run.total),
                total: run.total,
              })
            }}
          </p>
          <UiProgress :value="answered" :max="run.total" />
        </div>
        <UiCard pad>
          <QuizQuestion
            :question="question"
            :correction="correction"
            :correct="correct"
            :busy="busy"
            @submit="submit"
          />
        </UiCard>
        <div v-if="correction" class="mt-4 flex justify-end">
          <UiButton :label="upcoming ? $t('quiz.next') : $t('quiz.seeResult')" @click="next" />
        </div>
      </template>
    </template>
  </div>
</template>
