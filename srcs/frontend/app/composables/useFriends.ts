/* The friends graph (module-scoped). Socket frames trigger a full refetch
 * rather than partial patching. */

import type { Friend, PendingRequest, UserSummary } from '~/types'

const friends = ref<Friend[]>([])
const incoming = ref<PendingRequest[]>([])
const outgoing = ref<PendingRequest[]>([])
const loaded = ref(false)
let bound = false

function bind() {
  if (bound) return
  bound = true
  const { on } = useRealtime()
  on('friend.request', () => void refresh())
  on('friend.accepted', () => void refresh())
}

async function refresh() {
  const { api } = useApi()
  try {
    const [list, reqs] = await Promise.all([
      api<{ items: Friend[] }>('/api/v1/friends'),
      api<{ incoming: PendingRequest[]; outgoing: PendingRequest[] }>('/api/v1/friends/requests'),
    ])
    friends.value = list.items
    incoming.value = reqs.incoming
    outgoing.value = reqs.outgoing
    loaded.value = true
  } catch {
    // not authenticated or API down: retry on next mount
  }
}

export function useFriends() {
  bind()
  const { api } = useApi()

  async function sendRequest(addresseeId: number) {
    await api('/api/v1/friends/requests', { method: 'POST', body: { addressee_id: addresseeId } })
    await refresh()
  }

  async function accept(friendshipId: number) {
    await api(`/api/v1/friends/requests/${friendshipId}/accept`, { method: 'POST' })
    await refresh()
  }

  async function remove(friendshipId: number) {
    await api(`/api/v1/friends/${friendshipId}`, { method: 'DELETE' })
    await refresh()
  }

  async function block(userId: number) {
    await api('/api/v1/friends/block', { method: 'POST', body: { user_id: userId } })
    await refresh()
  }

  async function unblock(userId: number) {
    await api(`/api/v1/friends/block/${userId}`, { method: 'DELETE' })
    await refresh()
  }

  function searchUsers(q: string) {
    return api<UserSummary[]>('/api/v1/users', { query: { q } })
  }

  return {
    friends: readonly(friends),
    incoming: readonly(incoming),
    outgoing: readonly(outgoing),
    loaded: readonly(loaded),
    pendingCount: computed(() => incoming.value.length),
    refresh,
    sendRequest,
    accept,
    remove,
    block,
    unblock,
    searchUsers,
  }
}
