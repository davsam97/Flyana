<script setup lang="ts">
import type { Standing } from '~/composables/useMultiplayer'

const {
  ranking,
  winner,
  reason,
  meId,
  matchId = null,
} = defineProps<{
  ranking: Standing[]
  winner: Standing | null
  reason: string | null
  meId: number | null
  matchId?: string | null
}>()

const emit = defineEmits<{
  again: []
}>()

const { summary, loading, failed, load } = useMatchSummary()

const won = computed(() => winner !== null && winner.userId === meId)
const myRank = computed(() => ranking.findIndex((standing) => standing.userId === meId) + 1)
const myScore = computed(() => ranking.find((standing) => standing.userId === meId)?.score ?? 0)

const heading = ref<HTMLElement>()
onMounted(() => {
  heading.value?.focus()
  if (matchId) load(matchId)
})
</script>

<template>
  <UiCard pad>
    <div class="mb-5 flex flex-col items-center text-center">
      <span
        aria-hidden="true"
        class="mb-3 flex size-[64px] items-center justify-center rounded-full"
        :class="won ? 'bg-accent-3-soft text-accent-3' : 'bg-accent-soft text-accent'"
      >
        <Icon :name="won ? 'lucide:trophy' : 'lucide:flag'" mode="svg" size="2em" />
      </span>
      <h2 ref="heading" tabindex="-1" class="text-2xl font-semibold focus-visible:outline-none">
        {{ won ? $t('multiplayer.result.won') : $t('multiplayer.result.title') }}
      </h2>
      <p v-if="winner && !won" class="mt-1 text-fg-muted">
        {{ $t('multiplayer.result.winner', { name: winner.displayName }) }}
      </p>
    </div>

    <UiCallout v-if="reason === 'forfeit'" tone="hint" icon="lucide:user-x" class="mb-5">
      {{ $t('multiplayer.result.forfeit') }}
    </UiCallout>

    <div v-if="myRank > 0" class="mb-5 grid grid-cols-2 gap-4 border-y border-line-subtle py-4">
      <UiStat :value="`${myRank} / ${ranking.length}`" :label="$t('multiplayer.result.rank')" />
      <UiStat :value="myScore" :label="$t('multiplayer.result.score')" />
    </div>

    <MultiplayerStandings :ranking="ranking" :me-id="meId" class="mb-5" />

    <p v-if="loading" class="mb-5 text-sm text-fg-muted">{{ $t('multiplayer.recap.loading') }}</p>
    <UiCallout v-else-if="failed" tone="hint" icon="lucide:triangle-alert" class="mb-5">
      {{ $t('multiplayer.recap.failed') }}
    </UiCallout>
    <MultiplayerRecap v-else-if="summary" :summary="summary" :me-id="meId" class="mb-5" />

    <div class="flex justify-end">
      <UiButton :label="$t('multiplayer.result.again')" @click="emit('again')">
        <Icon name="lucide:rotate-ccw" mode="svg" size="1em" />
      </UiButton>
    </div>
  </UiCard>
</template>
