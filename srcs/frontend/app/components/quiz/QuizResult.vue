<script setup lang="ts">
import type { RunResult } from '~/types'

const {
  result,
  moduleSlug,
  xp = 0,
} = defineProps<{
  result: RunResult
  moduleSlug: string
  xp?: number
}>()

defineEmits<{ retry: [] }>()

const score = computed(() => percent(result.correct / Math.max(1, result.total)))
</script>

<template>
  <UiCard pad class="flex flex-col items-center gap-4 text-center">
    <span
      aria-hidden="true"
      class="flex size-16 items-center justify-center rounded-full"
      :class="result.passed ? 'bg-success-soft text-success' : 'bg-accent-soft text-accent'"
    >
      <Icon :name="result.passed ? 'lucide:rocket' : 'lucide:refresh-cw'" mode="svg" size="2em" />
    </span>
    <div>
      <h2 class="text-2xl font-semibold">
        {{ result.passed ? $t('quiz.passedTitle') : $t('quiz.failedTitle') }}
      </h2>
      <p class="mt-1 text-fg-muted">
        {{ $t('quiz.score', { correct: result.correct, total: result.total, n: score }) }}
      </p>
      <p class="mt-1 text-sm text-fg-subtle">
        {{ $t('quiz.passRule', { n: percent(result.pass_ratio) }) }}
      </p>
      <p v-if="xp > 0" class="mt-2 font-mono text-sm text-accent-3">
        {{ $t('quiz.xpGained', { n: xp }) }}
      </p>
    </div>
    <div class="flex flex-wrap justify-center gap-3">
      <UiButton :label="$t('quiz.retry')" variant="secondary" @click="$emit('retry')" />
      <UiButton :label="$t('quiz.backToModule')" :to="`/modules/${moduleSlug}`" />
    </div>
  </UiCard>
</template>
