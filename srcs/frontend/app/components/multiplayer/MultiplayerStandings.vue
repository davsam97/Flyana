<script setup lang="ts">
import type { Standing } from '~/composables/useMultiplayer'

/* `answeredBy` marks who answered, without revealing whether they were right */
const {
  ranking,
  meId,
  answeredBy = [],
  showAnswered = false,
} = defineProps<{
  ranking: Standing[]
  meId: number | null
  answeredBy?: number[]
  showAnswered?: boolean
}>()

type Place = 'first' | 'second' | 'third' | 'other'

const PLACES: Record<Place, string> = {
  first: 'bg-accent-3-soft text-accent-3',
  second: 'bg-accent-2-soft text-accent-2',
  third: 'bg-accent-soft text-accent',
  other: 'bg-surface-raised text-fg-subtle',
}

const ROWS = {
  me: 'bg-accent-soft',
  other: '',
}

function placeOf(index: number): Place {
  return (['first', 'second', 'third'] as const)[index] ?? 'other'
}
</script>

<template>
  <ol class="flex flex-col gap-1">
    <li
      v-for="(standing, index) in ranking"
      :key="standing.userId"
      class="flex items-center gap-3 rounded-md px-3 py-2"
      :class="standing.userId === meId ? ROWS.me : ROWS.other"
    >
      <span
        class="flex size-[24px] flex-none items-center justify-center rounded-full font-mono text-xs font-semibold"
        :class="PLACES[placeOf(index)]"
      >
        {{ index + 1 }}
      </span>
      <UiAvatar :name="standing.displayName" :src="standing.avatarPath" :size="28" />
      <span class="min-w-0 flex-1 truncate text-sm font-medium">
        {{ standing.displayName }}
        <span v-if="standing.userId === meId" class="text-fg-subtle">
          · {{ $t('multiplayer.you') }}
        </span>
      </span>
      <Icon
        v-if="showAnswered && answeredBy.includes(standing.userId)"
        name="lucide:circle-check"
        mode="svg"
        size="1em"
        class="flex-none text-success"
        :aria-label="$t('multiplayer.round.hasAnswered')"
      />
      <span class="font-mono text-sm font-semibold tabular-nums">{{ standing.score }}</span>
    </li>
  </ol>
</template>
