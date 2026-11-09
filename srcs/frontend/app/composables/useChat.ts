/* Direct chat state, shared app-wide.
 *
 * REST is the source of truth; socket frames only patch what is loaded. A sent
 * message is appended from the POST response and de-duplicated by id when its
 * socket echo arrives.
 */

import type { Conversation, DirectMessage } from '~/types'

const conversations = ref<Conversation[]>([])
const threads = reactive(new Map<number, DirectMessage[]>())
const cursors = reactive(new Map<number, number | null>()) // peer -> next `before`, null = start reached
const typing = reactive(new Set<number>()) // peer ids currently typing at me
const typingTimers = new Map<number, ReturnType<typeof setTimeout>>()

let bound = false
let myId = 0
let activePeerId = 0 // the thread currently on screen, 0 = none

function threadFor(peer: number): DirectMessage[] {
  if (!threads.has(peer)) threads.set(peer, [])
  return threads.get(peer)!
}

function peerOf(message: DirectMessage): number {
  return message.sender_id === myId ? message.recipient_id : message.sender_id
}

function appendToThread(peer: number, message: DirectMessage) {
  const list = threadFor(peer)
  if (list.some((m) => m.id === message.id)) return
  list.push(message)
}

async function loadConversations() {
  const { api } = useApi()
  try {
    conversations.value = await api<Conversation[]>('/api/v1/chat/conversations')
  } catch {
    // not authenticated: leave the list empty
  }
}

function bumpConversation(message: DirectMessage, seen = false) {
  const peer = peerOf(message)
  const existing = conversations.value.find((c) => c.user.id === peer)
  if (!existing) {
    // first message with someone we have no summary for: refetch the list
    void loadConversations()
    return
  }
  existing.last_message = message
  if (message.recipient_id === myId && !seen) existing.unread += 1
  conversations.value = [existing, ...conversations.value.filter((c) => c.user.id !== peer)]
}

function markThreadRead(peer: number) {
  for (const m of threadFor(peer)) {
    if (m.sender_id === myId && m.read_at === null) m.read_at = new Date().toISOString()
  }
}

function flagTyping(peer: number) {
  typing.add(peer)
  clearTimeout(typingTimers.get(peer))
  typingTimers.set(
    peer,
    setTimeout(() => typing.delete(peer), 4000),
  )
}

function bind() {
  if (bound) return
  bound = true
  const { on } = useRealtime()

  on('chat.message', (frame) => {
    const message = frame.message as DirectMessage | undefined
    if (!message) return
    const peer = peerOf(message)
    typing.delete(peer)
    if (threads.has(peer)) appendToThread(peer, message)

    const inView = peer === activePeerId && message.recipient_id === myId
    if (inView) {
      // I'm looking at this thread: acknowledge on the server, don't badge it
      message.read_at = new Date().toISOString()
      void useApi()
        .api(`/api/v1/chat/with/${peer}/read`, { method: 'POST' })
        .catch(() => {})
    }
    bumpConversation(message, inView)
  })

  on('chat.read', (frame) => {
    const peer = Number(frame.user_id)
    if (Number.isFinite(peer)) markThreadRead(peer)
  })

  on('chat.typing', (frame) => {
    const peer = Number(frame.user_id)
    if (Number.isFinite(peer)) flagTyping(peer)
  })
}

export function useChat() {
  const { api } = useApi()
  const { load: loadMe } = useMe()

  async function init() {
    const me = await loadMe()
    if (me) myId = me.id
    bind()
    await loadConversations()
  }

  async function openThread(peer: number) {
    bind()
    activePeerId = peer
    const page = await api<{ items: DirectMessage[]; next_before: number | null }>(
      `/api/v1/chat/with/${peer}`,
    )
    threads.set(peer, [...page.items])
    cursors.set(peer, page.next_before)
    const convo = conversations.value.find((c) => c.user.id === peer)
    if (convo) convo.unread = 0
  }

  function blur() {
    activePeerId = 0
  }

  async function loadOlder(peer: number) {
    const before = cursors.get(peer)
    if (!before) return
    const page = await api<{ items: DirectMessage[]; next_before: number | null }>(
      `/api/v1/chat/with/${peer}`,
      { query: { before } },
    )
    threads.set(peer, [...page.items, ...threadFor(peer)])
    cursors.set(peer, page.next_before)
  }

  async function send(peer: number, body: string) {
    const trimmed = body.trim()
    if (!trimmed) return
    const message = await api<DirectMessage>('/api/v1/chat/messages', {
      method: 'POST',
      body: { recipient_id: peer, body: trimmed },
    })
    appendToThread(peer, message)
    bumpConversation(message)
  }

  function notifyTyping(peer: number) {
    useRealtime().send({ type: 'chat.typing', to: peer })
  }

  return {
    conversations: readonly(conversations),
    unreadTotal: computed(() => conversations.value.reduce((sum, c) => sum + c.unread, 0)),
    init,
    loadConversations,
    openThread,
    blur,
    loadOlder,
    send,
    notifyTyping,
    thread: (peer: number) => computed(() => threads.get(peer) ?? []),
    hasOlder: (peer: number) => computed(() => cursors.get(peer) != null),
    isTyping: (peer: number) => computed(() => typing.has(peer)),
  }
}
