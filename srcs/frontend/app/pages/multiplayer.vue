<script setup lang="ts">
definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { t, te } = useI18n()
const { user } = useAuth()

const {
  connected,
  phase,
  roomId,
  maxPlayers,
  players,
  error,
  question,
  answered,
  pickedChoice,
  correctChoice,
  answeredBy,
  ranking,
  finishReason,
  winner,
  remainingSeconds,
  topics,
  questionCount,
  reconnect,
  clearError,
  createRoom,
  joinRoom,
  setReady,
  answer,
  leaveRoom,
} = useMultiplayer()

const meId = computed(() => user.value?.id ?? null)

// "connecting" is the normal first beat after login, not worth a warning
const realtimeStatus = useRealtime().status
const offline = computed(() => realtimeStatus.value === 'offline')

const errorMessage = computed(() => {
  if (!error.value) return ''
  const key = `multiplayer.errors.${error.value}`
  return te(key) ? t(key) : t('multiplayer.errors.generic')
})
</script>

<template>
  <div class="mx-auto w-full" :class="phase === 'setup' ? 'max-w-260' : 'max-w-240'">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl sm:text-3xl">{{ $t('nav.multiplayer') }}</h1>
      <UiTag
        v-if="roomId && phase !== 'setup'"
        type="neutral"
        :label="$t(`multiplayer.phase.${phase}`)"
        dot
      />
    </div>

    <div class="mb-5 flex flex-col gap-3 empty:hidden">
      <UiCallout
        v-if="offline"
        tone="hint"
        icon="lucide:wifi-off"
        :title="$t('multiplayer.offline.title')"
      >
        <p>{{ $t('multiplayer.offline.body') }}</p>
        <UiButton
          variant="secondary"
          size="sm"
          class="mt-3"
          :label="$t('multiplayer.offline.retry')"
          @click="reconnect"
        />
      </UiCallout>

      <UiCallout v-if="errorMessage" tone="danger" icon="lucide:circle-alert">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span>{{ errorMessage }}</span>
          <UiButton
            variant="ghost"
            size="sm"
            class="-my-1.5"
            :label="$t('multiplayer.dismiss')"
            @click="clearError"
          />
        </div>
      </UiCallout>
    </div>

    <template v-if="phase === 'setup'">
      <MultiplayerSetup
        :disabled="!connected"
        @create="(p) => createRoom(p.size, p.topics, p.questionCount)"
        @join="joinRoom"
      >
        <template #aside>
          <UiCard pad>
            <div class="mb-3 flex items-center gap-2">
              <Icon
                name="lucide:scroll-text"
                mode="svg"
                size="1.25em"
                class="text-accent"
                aria-hidden="true"
              />
              <h2 class="text-lg font-semibold">{{ $t('multiplayer.rules.title') }}</h2>
            </div>
            <ul class="flex flex-col gap-3 text-base text-fg-muted">
              <li
                v-for="rule in ['same', 'timer', 'speed', 'wrong', 'win']"
                :key="rule"
                class="flex gap-2"
              >
                <Icon
                  name="lucide:dot"
                  mode="svg"
                  size="1.25em"
                  class="flex-none text-accent"
                  aria-hidden="true"
                />
                {{ $t(`multiplayer.rules.${rule}`) }}
              </li>
            </ul>
          </UiCard>
        </template>
      </MultiplayerSetup>
    </template>

    <MultiplayerLobby
      v-else-if="phase === 'lobby' && roomId"
      :room-id="roomId"
      :players="players"
      :max-players="maxPlayers"
      :me-id="meId"
      :topics="topics"
      :question-count="questionCount"
      @ready="setReady"
      @leave="leaveRoom"
    />

    <div
      v-else-if="phase === 'playing'"
      class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_300px]"
    >
      <MultiplayerRound
        v-if="question"
        :question="question"
        :remaining-seconds="remainingSeconds"
        :answered="answered"
        :picked-choice="pickedChoice"
        :correct-choice="correctChoice"
        :answered-count="answeredBy.length"
        :player-count="players.length || ranking.length"
        @answer="answer"
      />
      <UiCard v-else pad>
        <p class="text-center text-sm text-fg-muted">{{ $t('multiplayer.round.loading') }}</p>
      </UiCard>

      <aside>
        <UiCard pad>
          <h2 class="mb-3 text-sm font-semibold text-fg-muted">
            {{ $t('multiplayer.standings') }}
          </h2>
          <MultiplayerStandings
            :ranking="ranking"
            :me-id="meId"
            :answered-by="answeredBy"
            show-answered
          />
        </UiCard>
        <UiButton
          variant="ghost"
          size="sm"
          class="mt-3"
          :label="$t('multiplayer.leave')"
          @click="leaveRoom"
        >
          <Icon name="lucide:log-out" mode="svg" size="1em" />
        </UiButton>
      </aside>
    </div>

    <MultiplayerResult
      v-else-if="phase === 'finished'"
      :ranking="ranking"
      :winner="winner"
      :reason="finishReason"
      :me-id="meId"
      :match-id="roomId"
      @again="leaveRoom"
    />
  </div>
</template>
