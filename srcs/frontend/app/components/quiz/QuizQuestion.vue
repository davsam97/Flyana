<script setup lang="ts">
import type { Correction, QuizQuestion } from '~/types'

export type QuizAnswerBody = { choice_ids: number[] } | { value: string }

const {
  question,
  correction = null,
  correct = null,
  busy = false,
} = defineProps<{
  question: QuizQuestion
  // Set once the answer is graded: the question then shows its correction
  correction?: Correction | null
  correct?: boolean | null
  busy?: boolean
}>()

const emit = defineEmits<{ submit: [body: QuizAnswerBody] }>()

const { t } = useI18n()

const selected = ref<number[]>([])
const typed = ref('')
const invalid = ref(false)

// A new question starts blank
watch(
  () => question.id,
  () => {
    selected.value = []
    typed.value = ''
    invalid.value = false
  },
)

const answered = computed(() => correction !== null)
const multiple = computed(() => question.kind === 'multi_choice')
const difficulty = computed(() => difficultyOf(question.difficulty_rating))

const hint = computed(() => {
  if (question.kind === 'numeric') return t('quiz.hintNumeric', { unit: question.unit ?? '' })
  return multiple.value ? t('quiz.hintMulti') : t('quiz.hintSingle')
})

const ready = computed(() =>
  question.kind === 'numeric' ? typed.value.trim() !== '' : selected.value.length > 0,
)

function toggle(id: number) {
  if (answered.value) return
  if (multiple.value) {
    selected.value = selected.value.includes(id)
      ? selected.value.filter((choice) => choice !== id)
      : [...selected.value, id]
  } else {
    selected.value = [id]
  }
}

function submit() {
  if (answered.value || busy || !ready.value) return
  if (question.kind === 'numeric') {
    const value = parseNumber(typed.value)
    invalid.value = value === null
    if (value !== null) emit('submit', { value })
  } else {
    emit('submit', { choice_ids: selected.value })
  }
}

function choiceState(id: number): 'right' | 'wrong' | 'missed' | 'idle' | 'chosen' {
  const chosen = selected.value.includes(id)
  if (!correction) return chosen ? 'chosen' : 'idle'
  const isRight = correction.correct_choice_ids.includes(id)
  if (isRight) return chosen ? 'right' : 'missed'
  return chosen ? 'wrong' : 'idle'
}

const CHOICE_STYLES = {
  idle: 'border-line-subtle',
  chosen: 'border-accent bg-accent-soft',
  right: 'border-success bg-success-soft',
  missed: 'border-success border-dashed',
  wrong: 'border-danger bg-danger-soft',
} as const

function tolerance(correction: Correction): string {
  return correction.tolerance_rel === null ? '' : `± ${percent(correction.tolerance_rel)} %`
}
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="submit">
    <div class="flex flex-wrap items-center gap-2">
      <UiTag :type="DIFFICULTY_TAG[difficulty]" :label="$t(`course.difficulty.${difficulty}`)" />
      <span class="text-xs text-fg-subtle">{{ hint }}</span>
    </div>

    <!-- eslint-disable-next-line vue/no-v-html -->
    <p class="text-lg leading-relaxed font-semibold" v-html="renderInline(question.stem ?? '')" />

    <fieldset v-if="question.kind !== 'numeric'" class="flex flex-col gap-2.5">
      <legend class="sr-only">{{ hint }}</legend>
      <label
        v-for="choice in question.choices"
        :key="choice.id"
        class="flex cursor-pointer items-start gap-3 rounded-md border px-4 py-3 text-sm transition-colors has-focus-visible:shadow-focus"
        :class="[
          CHOICE_STYLES[choiceState(choice.id)],
          answered ? 'cursor-default' : 'hover:bg-surface-hover',
        ]"
      >
        <input
          :type="multiple ? 'checkbox' : 'radio'"
          :name="`question-${question.id}`"
          :value="choice.id"
          :checked="selected.includes(choice.id)"
          :disabled="answered"
          class="mt-0.5 accent-(--accent)"
          @change="toggle(choice.id)"
        />
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span class="flex-1" v-html="renderInline(choice.text)" />
        <Icon
          v-if="choiceState(choice.id) === 'right' || choiceState(choice.id) === 'missed'"
          name="lucide:circle-check"
          mode="svg"
          class="flex-none text-success"
          :aria-label="$t('quiz.rightChoice')"
        />
        <Icon
          v-else-if="choiceState(choice.id) === 'wrong'"
          name="lucide:circle-x"
          mode="svg"
          class="flex-none text-danger"
          :aria-label="$t('quiz.wrongChoice')"
        />
      </label>
    </fieldset>

    <div v-else class="flex flex-col gap-1.5">
      <label :for="`numeric-${question.id}`" class="text-sm font-medium">
        {{ $t('quiz.yourValue') }}
      </label>
      <div class="flex items-center gap-2">
        <input
          :id="`numeric-${question.id}`"
          v-model="typed"
          type="text"
          inputmode="decimal"
          autocomplete="off"
          :disabled="answered"
          :aria-invalid="invalid"
          class="h-7 w-48 rounded-md border border-line-strong bg-surface-raised px-3 font-mono text-sm focus-visible:shadow-focus focus-visible:outline-none"
        />
        <span v-if="question.unit" class="font-mono text-sm text-fg-muted">{{
          question.unit
        }}</span>
      </div>
      <p v-if="invalid" class="text-xs text-danger">{{ $t('quiz.notANumber') }}</p>
    </div>

    <UiButton
      v-if="!answered"
      type="submit"
      :label="$t('quiz.check')"
      :disabled="!ready || busy"
      class="self-start"
    />

    <UiCallout
      v-if="correction"
      :tone="correct ? 'success' : 'danger'"
      :icon="correct ? 'lucide:circle-check-big' : 'lucide:circle-x'"
      :title="correct ? $t('quiz.right') : $t('quiz.wrong')"
    >
      <div class="flex flex-col gap-2 text-sm">
        <p v-if="correction.expected_value !== null" class="font-mono">
          {{ $t('quiz.expected') }} {{ correction.expected_value }} {{ correction.unit ?? '' }}
          <span class="text-fg-subtle">({{ tolerance(correction) }})</span>
        </p>
        <CourseMarkdown
          v-if="correction.explanation"
          :source="correction.explanation"
          class="text-sm"
        />
        <p v-if="correction.source" class="text-xs text-fg-subtle">
          {{ $t('quiz.source') }}
          <a
            v-if="correction.source.url"
            :href="correction.source.url"
            target="_blank"
            rel="noopener noreferrer"
            class="underline hover:text-fg-body"
            >{{ correction.source.label }}</a
          >
          <span v-else>{{ correction.source.label }}</span>
        </p>
      </div>
    </UiCallout>
  </form>
</template>
