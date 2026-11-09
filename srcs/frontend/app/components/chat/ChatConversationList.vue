<script setup lang="ts">
const { activeId } = defineProps<{ activeId: number | null }>()
const emit = defineEmits<{ select: [userId: number] }>()

const chat = useChat()

function preview(body: string) {
  return body.length > 48 ? `${body.slice(0, 48)}…` : body
}
</script>

<template>
  <div class="flex h-full w-full flex-col">
    <p v-if="chat.conversations.value.length === 0" class="p-4 text-sm text-fg-subtle">
      {{ $t('chat.noConversations') }}
    </p>

    <ul class="flex-1 overflow-y-auto">
      <li v-for="conversation in chat.conversations.value" :key="conversation.user.id">
        <button
          type="button"
          class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-surface-hover"
          :class="activeId === conversation.user.id ? 'bg-surface-hover' : ''"
          @click="emit('select', conversation.user.id)"
        >
          <UiAvatar :name="conversation.user.display_name" :size="36" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-sm font-semibold">
                {{ conversation.user.display_name }}
              </span>
              <span
                v-if="conversation.unread > 0"
                class="flex-none rounded-full bg-accent px-1.5 text-xs font-semibold text-on-accent"
              >
                {{ conversation.unread }}
              </span>
            </div>
            <p class="truncate text-xs text-fg-subtle">
              {{ preview(conversation.last_message.body) }}
            </p>
          </div>
        </button>
      </li>
    </ul>
  </div>
</template>
