<script setup lang="ts">
import type { UserSummary } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const chat = useChat()
const { api } = useApi()

const activePeer = ref<UserSummary | null>(null)

onMounted(async () => {
  await chat.init()
  const to = Number(route.query.to)
  if (Number.isFinite(to) && to > 0) await selectPeer(to)
})

onBeforeUnmount(() => chat.blur())

async function selectPeer(id: number) {
  const known = chat.conversations.value.find((c) => c.user.id === id)
  if (known) {
    activePeer.value = known.user
  } else {
    try {
      const profile = await api<UserSummary>(`/api/v1/users/${id}`)
      activePeer.value = {
        id: profile.id,
        display_name: profile.display_name,
        avatar_path: profile.avatar_path,
      }
    } catch {
      activePeer.value = null
      return
    }
  }
  if (Number(route.query.to) !== id) router.replace({ query: { to: id } })
}

// Below `md` only one pane shows at a time: this brings the list back
function closePeer() {
  activePeer.value = null
  router.replace({ query: {} })
}
</script>

<template>
  <div class="mx-auto w-full max-w-260">
    <h1 class="mb-4 text-2xl font-semibold">{{ $t('nav.messages') }}</h1>

    <UiCard class="flex h-[calc(100dvh-11rem)] min-h-96 overflow-hidden lg:h-[74dvh]">
      <div
        class="w-full flex-none md:w-72 md:border-r md:border-line-subtle"
        :class="activePeer ? 'hidden md:block' : ''"
      >
        <ChatConversationList :active-id="activePeer?.id ?? null" @select="selectPeer" />
      </div>

      <ChatWindow v-if="activePeer" :key="activePeer.id" :peer="activePeer" @back="closePeer" />
      <div
        v-else
        class="hidden flex-1 items-center justify-center p-8 text-sm text-fg-subtle md:flex"
      >
        {{ $t('chat.pickConversation') }}
      </div>
    </UiCard>
  </div>
</template>
