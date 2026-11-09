<script setup lang="ts">
import type { Leaderboard } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { api } = useApi()

const board = ref<Leaderboard | null>(null)
const loadError = ref(false)

onMounted(async () => {
  try {
    board.value = await api<Leaderboard>('/api/v1/gamification/leaderboard')
  } catch {
    loadError.value = true
  }
})

/* the caller's row is only repeated below the list when the top misses it */
const meInTop = computed(
  () => !!board.value?.me && board.value.entries.some((e) => e.id === board.value?.me?.id),
)

const PODIUM: Record<number, string> = {
  1: 'text-warning',
  2: 'text-fg-muted',
  3: 'text-accent',
}
</script>

<template>
  <div class="mx-auto w-full max-w-200 space-y-6">
    <div>
      <h1 class="text-2xl font-semibold">{{ $t('leaderboard.title') }}</h1>
      <p class="text-sm text-fg-subtle">{{ $t('leaderboard.subtitle') }}</p>
    </div>

    <UiCallout v-if="loadError" tone="danger" icon="lucide:circle-alert">
      {{ $t('leaderboard.loadError') }}
    </UiCallout>

    <template v-else-if="board">
      <UiCallout v-if="board.me" tone="info" icon="lucide:trophy">
        {{ $t('leaderboard.yourRank', { n: board.me.rank }) }}
      </UiCallout>
      <UiCallout v-else tone="info" icon="lucide:sparkles">
        {{ $t('leaderboard.noXp') }}
      </UiCallout>

      <UiCard>
        <p v-if="!board.entries.length" class="px-4 py-6 text-center text-sm text-fg-subtle">
          {{ $t('leaderboard.empty') }}
        </p>
        <ol v-else class="divide-y divide-line-subtle">
          <li
            v-for="entry in board.entries"
            :key="entry.id"
            class="flex items-center gap-3 px-4 py-3"
            :class="entry.id === board.me?.id ? 'bg-accent-soft' : ''"
          >
            <span
              class="w-8 text-right font-mono text-sm font-semibold tabular-nums"
              :class="PODIUM[entry.rank] ?? 'text-fg-subtle'"
            >
              {{ entry.rank }}
            </span>
            <UiAvatar :name="entry.display_name" :src="entry.avatar_path" :size="32" />
            <div class="min-w-0 flex-1">
              <NuxtLink
                :to="entry.id === board.me?.id ? '/profil' : `/users/${entry.id}`"
                class="block truncate text-sm font-medium hover:underline"
              >
                {{ entry.display_name }}
                <span v-if="entry.id === board.me?.id" class="text-fg-subtle">
                  ({{ $t('leaderboard.you') }})
                </span>
              </NuxtLink>
              <p class="text-xs text-fg-subtle">
                {{ $t('leaderboard.level', { n: entry.level }) }}
              </p>
            </div>
            <span class="text-sm font-semibold tabular-nums">{{ entry.xp }} XP</span>
          </li>
        </ol>

        <div
          v-if="board.me && !meInTop"
          class="flex items-center gap-3 border-t border-line-strong bg-accent-soft px-4 py-3"
        >
          <span class="w-8 text-right font-mono text-sm font-semibold tabular-nums">
            {{ board.me.rank }}
          </span>
          <UiAvatar :name="board.me.display_name" :src="board.me.avatar_path" :size="32" />
          <div class="min-w-0 flex-1">
            <NuxtLink to="/profil" class="block truncate text-sm font-medium hover:underline">
              {{ board.me.display_name }}
              <span class="text-fg-subtle">({{ $t('leaderboard.you') }})</span>
            </NuxtLink>
            <p class="text-xs text-fg-subtle">
              {{ $t('leaderboard.level', { n: board.me.level }) }}
            </p>
          </div>
          <span class="text-sm font-semibold tabular-nums">{{ board.me.xp }} XP</span>
        </div>
      </UiCard>
    </template>
  </div>
</template>
