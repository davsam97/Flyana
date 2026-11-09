/* Which of my friends are online: REST snapshot, then socket transitions.
 * Subscribes before fetching so no transition is lost during the REST call. */

interface FriendRow {
  user: { id: number }
  online: boolean
}

const online = reactive(new Map<number, boolean>())
let bound = false
let hydrated = false

function bind() {
  if (bound) return
  bound = true
  useRealtime().on('presence', (message) => {
    const id = Number(message.user_id)
    if (Number.isFinite(id)) online.set(id, message.online === true)
  })
}

export function usePresence() {
  bind()

  const { api } = useApi()

  async function hydrate() {
    if (hydrated) return
    try {
      const { items } = await api<{ items: FriendRow[] }>('/api/v1/friends')
      for (const friend of items) {
        // a live transition already received wins over the REST snapshot
        if (!online.has(friend.user.id)) online.set(friend.user.id, friend.online)
      }
      hydrated = true
    } catch {
      // not authenticated or API unavailable: retried on the next mount
    }
  }

  return {
    hydrate,
    isOnline: (userId: number) => online.get(userId) === true,
  }
}
