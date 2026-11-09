<script setup lang="ts">
import type { UserSummary } from '~/types'

const { peer } = defineProps<{ peer: UserSummary }>()
const emit = defineEmits<{ back: [] }>()

const { t } = useI18n()
const chat = useChat()
const { me } = useMe()

const messages = chat.thread(peer.id)
const hasOlder = chat.hasOlder(peer.id)
const typing = chat.isTyping(peer.id)

const draft = ref('')
const sendError = ref('')
const scroller = ref<HTMLElement>()
let lastTypingSent = 0

watch(
  () => peer.id,
  (id) => chat.openThread(id),
  { immediate: true },
)

watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    scroller.value?.scrollTo({ top: scroller.value.scrollHeight })
  },
)

function onInput() {
  const now = Date.now()
  if (now - lastTypingSent > 2000) {
    chat.notifyTyping(peer.id)
    lastTypingSent = now
  }
}

async function handleSend() {
  const body = draft.value.trim()
  if (!body) return
  draft.value = ''
  sendError.value = ''
  try {
    await chat.send(peer.id, body)
  } catch (err) {
    draft.value = body
    sendError.value =
      httpStatus(err) === 403 ? t('chat.sendBlocked') : t(apiErrorKey(err) ?? 'chat.sendFailed')
  }
}

function mine(senderId: number) {
  return senderId === me.value?.id
}

function clock(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex h-full min-w-0 flex-1 flex-col">
    <header class="flex items-center gap-3 border-b border-line-subtle px-3 py-3 sm:px-5">
      <button
        type="button"
        class="inline-flex size-7 flex-none items-center justify-center rounded-md text-fg-muted transition-colors duration-fast hover:bg-surface-hover hover:text-fg-body focus-visible:shadow-focus focus-visible:outline-none md:hidden"
        :aria-label="$t('chat.back')"
        @click="emit('back')"
      >
        <Icon name="lucide:arrow-left" mode="svg" size="1.25em" aria-hidden="true" />
      </button>
      <UiAvatar :name="peer.display_name" :size="32" />
      <div class="min-w-0">
        <p class="truncate text-sm font-semibold">{{ peer.display_name }}</p>
        <UiPresenceDot :user-id="peer.id" label />
      </div>
    </header>

    <div ref="scroller" class="flex-1 space-y-2 overflow-y-auto px-3 py-4 sm:px-5">
      <button
        v-if="hasOlder"
        type="button"
        class="mx-auto block text-xs text-fg-subtle hover:text-fg-body"
        @click="chat.loadOlder(peer.id)"
      >
        {{ $t('chat.loadOlder') }}
      </button>

      <p v-if="messages.length === 0" class="py-8 text-center text-sm text-fg-subtle">
        {{ $t('chat.empty', { name: peer.display_name }) }}
      </p>

      <div
        v-for="message in messages"
        :key="message.id"
        class="flex"
        :class="mine(message.sender_id) ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[85%] rounded-lg px-3 py-2 text-sm sm:max-w-[75%]"
          :class="
            mine(message.sender_id) ? 'bg-accent text-on-accent' : 'bg-surface-raised text-fg-body'
          "
        >
          <p class="whitespace-pre-wrap break-words">{{ message.body }}</p>
          <p
            class="mt-1 text-right text-[10px]"
            :class="mine(message.sender_id) ? 'text-on-accent/70' : 'text-fg-subtle'"
          >
            {{ clock(message.created_at) }}
            <span v-if="mine(message.sender_id) && message.read_at"> · {{ $t('chat.read') }}</span>
          </p>
        </div>
      </div>

      <p v-if="typing" class="text-xs text-fg-subtle">
        {{ $t('chat.typing', { name: peer.display_name }) }}
      </p>
    </div>

    <div class="border-t border-line-subtle p-3 sm:p-4">
      <UiCallout v-if="sendError" tone="danger" class="mb-2">{{ sendError }}</UiCallout>
      <div class="flex items-end gap-2">
        <UiTextarea
          v-model="draft"
          class="min-h-9"
          :placeholder="$t('chat.placeholder')"
          @input="onInput"
          @keydown.enter.exact.prevent="handleSend"
        />
        <UiButton :label="$t('chat.send')" @click="handleSend" />
      </div>
    </div>
  </div>
</template>
