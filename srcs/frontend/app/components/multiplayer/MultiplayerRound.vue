<script setup lang="ts">
import type { MatchQuestion } from '~/composables/useMultiplayer'

/* `correctChoice` stays null until the server closes the question for everyone */
const {
  question,
  remainingSeconds,
  answered,
  pickedChoice,
  correctChoice,
  answeredCount,
  playerCount,
} = defineProps<{
  question: MatchQuestion
  remainingSeconds: number
  answered: boolean
  pickedChoice: number | null
  correctChoice: number | null
  answeredCount: number
  playerCount: number
}>()

const emit = defineEmits<{
  answer: [choiceId: number]
}>()

type ChoiceState = 'idle' | 'picked' | 'dimmed' | 'correct' | 'wrong'

const CHOICES: Record<ChoiceState, string> = {
  idle: 'border-line-strong bg-surface-raised hover:border-accent hover:bg-surface-hover',
  picked: 'border-accent bg-accent-soft',
  dimmed: 'border-line-subtle bg-surface-raised opacity-50',
  correct: 'border-success bg-success-soft',
  wrong: 'border-danger bg-danger-soft',
}

const BADGES: Record<ChoiceState, string> = {
  idle: 'bg-surface-card text-fg-muted',
  picked: 'bg-accent text-on-accent',
  dimmed: 'bg-surface-card text-fg-subtle',
  correct: 'bg-surface-card text-success',
  wrong: 'bg-surface-card text-danger',
}

const LETTERS = 'ABCDEFGH'

const revealed = computed(() => correctChoice !== null)

function stateOf(choiceId: number): ChoiceState {
  if (revealed.value) {
    if (choiceId === correctChoice) return 'correct'
    return choiceId === pickedChoice ? 'wrong' : 'dimmed'
  }
  if (!answered) return 'idle'
  return choiceId === pickedChoice ? 'picked' : 'dimmed'
}

type Verdict = 'correct' | 'wrong' | 'missed'

const VERDICTS: Record<
  Verdict,
  { tone: 'success' | 'danger' | 'hint'; icon: string; key: string }
> = {
  correct: { tone: 'success', icon: 'lucide:circle-check-big', key: 'multiplayer.round.correct' },
  wrong: { tone: 'danger', icon: 'lucide:circle-x', key: 'multiplayer.round.wrong' },
  missed: { tone: 'hint', icon: 'lucide:clock', key: 'multiplayer.round.missed' },
}

/* null after a reconnection: the pick is not restored, and saying "missed" to
   someone who did answer would be worse than saying nothing */
const verdict = computed(() => {
  if (pickedChoice !== null) {
    return pickedChoice === correctChoice ? VERDICTS.correct : VERDICTS.wrong
  }
  return answered ? null : VERDICTS.missed
})

type Urgency = 'calm' | 'hurry'
const urgency = computed<Urgency>(() => (remainingSeconds <= 5 ? 'hurry' : 'calm'))
const CLOCK: Record<Urgency, string> = {
  calm: 'text-fg-body',
  hurry: 'text-danger',
}

const heading = ref<HTMLElement>()
watch(
  () => question.id,
  () => nextTick(() => heading.value?.focus()),
)
</script>

<template>
  <div>
    <div class="mb-4">
      <div class="mb-2 flex flex-wrap items-baseline justify-between gap-3">
        <p class="font-mono text-xs text-fg-subtle">
          {{ $t('multiplayer.roundProgress', { n: question.number, total: question.total }) }}
        </p>
        <p role="timer" class="flex items-center gap-1.5 font-mono text-sm" :class="CLOCK[urgency]">
          <Icon name="lucide:timer" mode="svg" size="1em" aria-hidden="true" />
          <span class="sr-only">{{ $t('multiplayer.timeLeft') }}</span>
          {{ remainingSeconds }} s
        </p>
      </div>
      <UiProgress :value="remainingSeconds" :max="question.durationSeconds" />
    </div>

    <UiCard pad>
      <h2
        ref="heading"
        tabindex="-1"
        class="mb-5 text-lg leading-snug font-semibold break-words focus-visible:outline-none sm:text-xl"
      >
        <UiCodeText :text="question.text" />
      </h2>

      <div class="grid gap-3 sm:grid-cols-2">
        <button
          v-for="(choice, index) in question.choices"
          :key="choice.id"
          type="button"
          class="flex items-start gap-3 rounded-md border p-3 text-left text-sm transition-colors duration-fast focus-visible:shadow-focus focus-visible:outline-none disabled:cursor-default"
          :class="CHOICES[stateOf(choice.id)]"
          :disabled="answered || revealed"
          :aria-pressed="choice.id === pickedChoice"
          @click="emit('answer', choice.id)"
        >
          <span
            aria-hidden="true"
            class="flex size-[24px] flex-none items-center justify-center rounded-sm font-mono text-xs font-semibold"
            :class="BADGES[stateOf(choice.id)]"
          >
            {{ LETTERS[index] }}
          </span>
          <span class="min-w-0 pt-0.5 break-words"><UiCodeText :text="choice.text" /></span>
        </button>
      </div>

      <UiCallout
        v-if="revealed && verdict"
        :tone="verdict.tone"
        :icon="verdict.icon"
        class="mt-5"
        aria-live="polite"
      >
        {{ $t(verdict.key) }}
      </UiCallout>
      <UiCallout
        v-else-if="answered"
        tone="info"
        icon="lucide:hourglass"
        class="mt-5"
        aria-live="polite"
      >
        {{ $t('multiplayer.round.waiting', { n: answeredCount, total: playerCount }) }}
      </UiCallout>
    </UiCard>
  </div>
</template>
