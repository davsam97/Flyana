<script setup lang="ts">
import type { MatchSummary, MatchSummaryChoice, MatchSummaryQuestion } from '~/types'

const { summary, meId } = defineProps<{
  summary: MatchSummary
  meId: number | null
}>()

type ChoiceStyle = 'correct' | 'wrong' | 'plain'

const CHOICE_ROWS: Record<ChoiceStyle, string> = {
  correct: 'border-success bg-surface-raised',
  wrong: 'border-danger bg-surface-raised',
  plain: 'border-transparent',
}

interface PlayerRow {
  userId: number
  name: string
  answered: boolean
  seconds: string
  points: number
}

function myChoiceId(question: MatchSummaryQuestion): number | null {
  return question.attempts.find((attempt) => attempt.user_id === meId)?.choice_id ?? null
}

function choiceStyle(question: MatchSummaryQuestion, choice: MatchSummaryChoice): ChoiceStyle {
  if (myChoiceId(question) !== choice.id) return 'plain'
  return choice.correct ? 'correct' : 'wrong'
}

function rowsFor(question: MatchSummaryQuestion): PlayerRow[] {
  return summary.players.map((player) => {
    const attempt = question.attempts.find((entry) => entry.user_id === player.user_id)
    return {
      userId: player.user_id,
      name: player.display_name,
      answered: attempt !== undefined && attempt.response_ms !== null,
      seconds: ((attempt?.response_ms ?? 0) / 1000).toFixed(1),
      points: attempt?.score ?? 0,
    }
  })
}
</script>

<template>
  <div>
    <h3 class="mb-3 text-sm font-semibold text-fg-muted">{{ $t('multiplayer.recap.title') }}</h3>
    <div class="flex flex-col gap-5">
      <div
        v-for="question in summary.questions"
        :key="question.position"
        class="flex flex-col gap-2"
      >
        <div class="flex items-start gap-2">
          <span class="flex-none text-xs font-semibold whitespace-nowrap text-fg-subtle">
            {{ $t('multiplayer.recap.round', { n: question.position }) }}
          </span>
          <p
            :lang="question.is_fallback ? 'en' : undefined"
            class="min-w-0 text-sm font-semibold break-words"
          >
            <UiCodeText :text="question.stem" />
          </p>
        </div>

        <ul class="flex flex-col gap-1">
          <li
            v-for="choice in question.choices"
            :key="choice.id"
            class="flex items-center gap-2 rounded-md border-l-2 px-3 py-2 text-sm"
            :class="CHOICE_ROWS[choiceStyle(question, choice)]"
          >
            <span class="min-w-0 flex-1">
              <UiCodeText :text="choice.text" />
            </span>
            <span v-if="choice.correct" class="flex-none text-success">
              <Icon name="lucide:circle-check-big" mode="svg" size="1em" aria-hidden="true" />
              <span class="sr-only">{{ $t('multiplayer.recap.correctAnswer') }}</span>
            </span>
            <UiTag
              v-if="myChoiceId(question) === choice.id"
              type="neutral"
              :label="$t('multiplayer.recap.yourAnswer')"
              class="flex-none"
            />
          </li>
        </ul>

        <div class="flex flex-col gap-1 border-t border-line-subtle pt-2">
          <p v-for="row in rowsFor(question)" :key="row.userId" class="text-xs text-fg-subtle">
            <span class="font-medium">{{ row.name }}</span>
            ·
            {{
              row.answered
                ? $t('multiplayer.recap.answered', { seconds: row.seconds, points: row.points })
                : $t('multiplayer.recap.noAnswer')
            }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
