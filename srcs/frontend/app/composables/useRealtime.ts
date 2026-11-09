/* The app's single WebSocket, shared at module scope. Authenticated by the
 * `access_token` cookie sent with the same-origin handshake. */

export type RealtimeStatus = 'idle' | 'connecting' | 'online' | 'offline'

type Payload = Record<string, unknown>
type Handler = (message: Payload) => void

const PING_INTERVAL = 25_000
const MAX_BACKOFF = 30_000
const MAX_RECONNECT_WINDOW = 120_000
const JITTER_RATIO = 0.2

const status = ref<RealtimeStatus>('idle')
const latency = ref<number | null>(null)

let socket: WebSocket | null = null
let wanted = false
let attempts = 0
let reconnectStartedAt = 0
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let pingTimer: ReturnType<typeof setInterval> | null = null
let pingSentAt = 0
const handlers = new Map<string, Set<Handler>>()

function endpoint() {
  const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${scheme}//${location.host}/api/ws`
}

function dispatch(message: Payload) {
  const type = typeof message.type === 'string' ? message.type : ''
  if (type === 'pong') {
    latency.value = Math.round(performance.now() - pingSentAt)
    return
  }
  handlers.get(type)?.forEach((fn) => fn(message))
}

function clearTimers() {
  if (pingTimer) clearInterval(pingTimer)
  if (reconnectTimer) clearTimeout(reconnectTimer)
  pingTimer = null
  reconnectTimer = null
}

function connect() {
  if (!wanted || (socket && socket.readyState <= WebSocket.OPEN)) return

  status.value = 'connecting'
  socket = new WebSocket(endpoint())

  socket.onopen = () => {
    attempts = 0
    reconnectStartedAt = 0
    status.value = 'online'
    pingTimer = setInterval(() => {
      if (socket?.readyState !== WebSocket.OPEN) return
      pingSentAt = performance.now()
      socket.send(JSON.stringify({ type: 'ping' }))
    }, PING_INTERVAL)
  }

  socket.onmessage = (event) => {
    try {
      dispatch(JSON.parse(event.data))
    } catch {
      // non-JSON frame: off-protocol, ignore it
    }
  }

  socket.onclose = () => {
    clearTimers()
    socket = null
    latency.value = null
    if (!wanted) {
      status.value = 'idle'
      return
    }
    status.value = 'offline'
    if (reconnectStartedAt === 0) reconnectStartedAt = Date.now()
    if (Date.now() - reconnectStartedAt >= MAX_RECONNECT_WINDOW) return
    attempts += 1
    const backoff = Math.min(1000 * 2 ** attempts, MAX_BACKOFF)
    const jitter = backoff * JITTER_RATIO * (Math.random() * 2 - 1)
    reconnectTimer = setTimeout(connect, Math.max(250, backoff + jitter))
  }
}

export function useRealtime() {
  function start() {
    wanted = true
    reconnectStartedAt = 0
    connect()
  }

  function reconnect() {
    clearTimers()
    const previousSocket = socket
    socket = null
    attempts = 0
    reconnectStartedAt = 0
    wanted = false
    previousSocket?.close()
    wanted = true
    connect()
  }

  function stop() {
    wanted = false
    clearTimers()
    socket?.close()
    socket = null
    status.value = 'idle'
  }

  /* Subscribes to messages of a given `type`. Returns the unsubscribe
     function — call it from `onUnmounted` in the component. */
  function on(type: string, handler: Handler) {
    const set = handlers.get(type) ?? new Set<Handler>()
    set.add(handler)
    handlers.set(type, set)
    return () => set.delete(handler)
  }

  function send(message: Payload) {
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(message))
  }

  return {
    status: readonly(status),
    latency: readonly(latency),
    start,
    reconnect,
    stop,
    on,
    send,
  }
}
