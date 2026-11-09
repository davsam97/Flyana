<script setup lang="ts">
import type { LobbyPlayer } from '~/composables/useMultiplayer'

/* The server starts the match on its own once everyone (2 or more) is ready. */
const { roomId, players, maxPlayers, meId, topics, questionCount } = defineProps<{
  roomId: string
  players: LobbyPlayer[]
  maxPlayers: number
  meId: number | null
  topics: readonly string[]
  questionCount: number
}>()

const emit = defineEmits<{
  ready: [ready: boolean]
  leave: []
}>()

const { topics: allTopics, load: loadTopics } = usePlayableTopics()
const me = computed(() => players.find((player) => player.id === meId))
const readyCount = computed(() => players.filter((player) => player.ready).length)
const emptySeats = computed(() => Math.max(0, maxPlayers - players.length))
const waitingForPlayers = computed(() => players.length < 2)

const selectedTopicsLabel = computed(() => {
  if (topics.length === 0) {
    return ''
  }
  return topics
    .map((slug) => {
      const topic = allTopics.value.find((t) => t.slug === slug)
      return topic?.name ?? slug
    })
    .join(', ')
})

const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

async function copyCode() {
  try {
    await navigator.clipboard.writeText(roomId)
    copied.value = true
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => (copied.value = false), 2000)
  } catch {
    // clipboard refused (insecure context, permissions): the code stays readable
  }
}

onMounted(() => loadTopics())
onBeforeUnmount(() => clearTimeout(copiedTimer))
</script>

<template>
  <div class="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
    <UiCard pad class="flex flex-col items-start">
      <p class="mb-1.5 font-mono text-xs text-fg-subtle">{{ $t('multiplayer.lobby.code') }}</p>
      <p
        class="mb-3 font-mono text-3xl font-semibold tracking-caps break-all text-accent sm:text-4xl"
      >
        {{ roomId }}
      </p>
      <UiButton
        variant="secondary"
        size="sm"
        :label="copied ? $t('multiplayer.lobby.copied') : $t('multiplayer.lobby.copy')"
        @click="copyCode"
      >
        <Icon :name="copied ? 'lucide:check' : 'lucide:copy'" mode="svg" size="1em" />
      </UiButton>
      <p class="mt-5 text-sm text-fg-muted">{{ $t('multiplayer.lobby.share') }}</p>

      <p class="mt-5 text-sm text-fg-muted">
        {{ $t('multiplayer.lobby.questions', { n: questionCount }) }}
      </p>
      <p v-if="selectedTopicsLabel" class="text-sm text-fg-muted">
        {{ selectedTopicsLabel }}
      </p>
      <p v-else class="text-sm text-fg-muted">
        {{ $t('multiplayer.lobby.allLevels') }}
      </p>

      <div class="mt-auto w-full pt-6">
        <UiCallout
          :tone="waitingForPlayers ? 'hint' : 'info'"
          icon="lucide:info"
          aria-live="polite"
        >
          {{
            waitingForPlayers
              ? $t('multiplayer.lobby.needTwo')
              : $t('multiplayer.lobby.autoStart', { ready: readyCount, total: players.length })
          }}
        </UiCallout>
      </div>
    </UiCard>

    <UiCard>
      <div class="flex items-center justify-between border-b border-line-subtle px-4 py-4 sm:px-5">
        <h2 class="text-lg font-semibold">{{ $t('multiplayer.lobby.players') }}</h2>
        <span class="font-mono text-xs text-fg-subtle">
          {{ players.length }} / {{ maxPlayers }}
        </span>
      </div>

      <ul class="divide-y divide-line-subtle" aria-live="polite">
        <li
          v-for="player in players"
          :key="player.id"
          class="flex items-center gap-3 px-4 py-3 sm:px-5"
        >
          <UiAvatar
            :name="player.displayName"
            :src="player.avatarPath"
            :size="32"
            :ring="player.id === meId"
          />
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium">
              {{ player.displayName }}
              <span v-if="player.id === meId" class="text-fg-subtle">
                · {{ $t('multiplayer.you') }}
              </span>
            </p>
            <UiTag
              v-if="!player.connected"
              type="warning"
              dot
              :label="$t('multiplayer.lobby.reconnecting')"
            />
          </div>
          <UiTag
            :type="player.ready ? 'success' : 'neutral'"
            :label="player.ready ? $t('multiplayer.lobby.ready') : $t('multiplayer.lobby.notReady')"
            dot
          />
        </li>
        <li
          v-for="seat in emptySeats"
          :key="`seat-${seat}`"
          class="flex items-center gap-3 px-4 py-3 text-sm text-fg-subtle sm:px-5"
        >
          <span
            aria-hidden="true"
            class="flex size-[32px] items-center justify-center rounded-full border border-dashed border-line-strong"
          >
            <Icon name="lucide:user-plus" mode="svg" size="1em" />
          </span>
          {{ $t('multiplayer.lobby.emptySeat') }}
        </li>
      </ul>

      <div
        class="flex flex-wrap items-center justify-between gap-3 border-t border-line-subtle px-4 py-4 sm:px-5"
      >
        <UiButton variant="ghost" :label="$t('multiplayer.leave')" @click="emit('leave')">
          <Icon name="lucide:log-out" mode="svg" size="1em" />
        </UiButton>
        <UiButton
          :variant="me?.ready ? 'secondary' : 'primary'"
          :label="me?.ready ? $t('multiplayer.lobby.unready') : $t('multiplayer.lobby.imReady')"
          :disabled="!me"
          @click="emit('ready', !me?.ready)"
        >
          <Icon :name="me?.ready ? 'lucide:x' : 'lucide:check'" mode="svg" size="1em" />
        </UiButton>
      </div>
    </UiCard>
  </div>
</template>
