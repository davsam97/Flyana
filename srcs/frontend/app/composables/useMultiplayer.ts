/* Realtime quiz matches, on top of the app's single WebSocket.
 *
 * State lives at module scope, like `useRealtime`: leaving the page and coming
 * back mid-match finds the room where it was. The socket itself belongs to the
 * dashboard layout — this composable never opens nor closes it.
 */

export interface LobbyPlayer {
  id: number
  displayName: string
  avatarPath: string | null
  ready: boolean
  connected: boolean
}

export interface MatchQuestion {
  id: number
  text: string
  choices: Array<{ id: number; text: string }>
  number: number
  total: number
  durationSeconds: number
}

export interface Standing {
  userId: number
  displayName: string
  avatarPath: string | null
  score: number
}

export type MatchPhase = 'setup' | 'lobby' | 'playing' | 'finished'

type Payload = Record<string, unknown>

function isRecord(value: unknown): value is Payload {
  return typeof value === 'object' && value !== null
}

function playerFromMessage(player: Payload): LobbyPlayer | null {
  if (
    typeof player.id !== 'number' ||
    typeof player.display_name !== 'string' ||
    (typeof player.avatar_path !== 'string' && player.avatar_path !== null) ||
    typeof player.ready !== 'boolean' ||
    typeof player.connected !== 'boolean'
  ) {
    return null
  }

  return {
    id: player.id,
    displayName: player.display_name,
    avatarPath: player.avatar_path,
    ready: player.ready,
    connected: player.connected,
  }
}

function standingFromMessage(standing: Payload): Standing | null {
  if (
    typeof standing.user_id !== 'number' ||
    typeof standing.display_name !== 'string' ||
    (typeof standing.avatar_path !== 'string' && standing.avatar_path !== null) ||
    typeof standing.score !== 'number'
  ) {
    return null
  }

  return {
    userId: standing.user_id,
    displayName: standing.display_name,
    avatarPath: standing.avatar_path,
    score: standing.score,
  }
}

function parsePlayers(value: unknown): LobbyPlayer[] {
  if (!Array.isArray(value)) return []
  return value.filter(isRecord).flatMap((player) => {
    const parsed = playerFromMessage(player)
    return parsed === null ? [] : [parsed]
  })
}

function parseTopics(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.filter((slug): slug is string => typeof slug === 'string')
}

function parseStandings(value: unknown): Standing[] {
  if (!Array.isArray(value)) return []
  return value.filter(isRecord).flatMap((standing) => {
    const parsed = standingFromMessage(standing)
    return parsed === null ? [] : [parsed]
  })
}

const roomId = ref<string | null>(null)
const maxPlayers = ref(0)
const players = ref<LobbyPlayer[]>([])
const status = ref('waiting')
const error = ref<string | null>(null)
const matchStarted = ref(false)
const question = ref<MatchQuestion | null>(null)
const answered = ref(false)
const pickedChoice = ref<number | null>(null)
const answeredBy = ref<number[]>([])
const correctChoice = ref<number | null>(null)
const standings = ref<Standing[]>([])
const finished = ref(false)
const finishReason = ref<string | null>(null)
const winnerId = ref<number | null>(null)
const remainingSeconds = ref(0)
const topics = ref<string[]>([])
const questionCount = ref(0)

let countdownTimer: ReturnType<typeof setInterval> | null = null
let listening = false

function stopCountdown() {
  if (countdownTimer !== null) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startCountdown(durationSeconds: number) {
  stopCountdown()
  remainingSeconds.value = durationSeconds
  countdownTimer = setInterval(() => {
    if (remainingSeconds.value <= 1) {
      remainingSeconds.value = 0
      stopCountdown()
      return
    }

    remainingSeconds.value -= 1
  }, 1000)
}

function resetMatch() {
  roomId.value = null
  maxPlayers.value = 0
  players.value = []
  status.value = 'waiting'
  matchStarted.value = false
  question.value = null
  answered.value = false
  pickedChoice.value = null
  answeredBy.value = []
  correctChoice.value = null
  standings.value = []
  finished.value = false
  finishReason.value = null
  winnerId.value = null
  remainingSeconds.value = 0
  topics.value = []
  questionCount.value = 0
  stopCountdown()
}

function applyQuestionMessage(message: Payload) {
  if (
    typeof message.question_id !== 'number' ||
    typeof message.text !== 'string' ||
    typeof message.question_number !== 'number' ||
    typeof message.question_count !== 'number' ||
    typeof message.duration_seconds !== 'number' ||
    !Array.isArray(message.choices)
  ) {
    return false
  }

  const choices = message.choices.filter(
    (choice): choice is { id: number; text: string } =>
      isRecord(choice) && typeof choice.id === 'number' && typeof choice.text === 'string',
  )

  question.value = {
    id: message.question_id,
    text: message.text,
    choices,
    number: message.question_number,
    total: message.question_count,
    durationSeconds: message.duration_seconds,
  }
  matchStarted.value = true
  answered.value = false
  pickedChoice.value = null
  answeredBy.value = []
  correctChoice.value = null
  finished.value = false
  const remaining =
    typeof message.remaining_seconds === 'number'
      ? Math.max(0, Math.ceil(message.remaining_seconds))
      : message.duration_seconds
  startCountdown(remaining)
  return true
}

function applyFinished(message: Payload) {
  finished.value = true
  status.value = 'finished'
  question.value = null
  stopCountdown()
  remainingSeconds.value = 0
  finishReason.value = typeof message.reason === 'string' ? message.reason : 'normal'
  winnerId.value = typeof message.winner_id === 'number' ? message.winner_id : null

  if (Array.isArray(message.standings)) {
    standings.value = parseStandings(message.standings)
  }
}

/* Registers the match handlers once for the whole app lifetime: the socket
   outlives the page, so its messages must too. */
function listen() {
  if (listening) return
  listening = true

  const realtime = useRealtime()

  realtime.on('match.created', (message) => {
    if (typeof message.match_id === 'string') {
      resetMatch()
      roomId.value = message.match_id
      error.value = null
    }
  })

  realtime.on('match.lobby', (message) => {
    if (typeof message.match_id !== 'string') return

    roomId.value = message.match_id
    error.value = null
    if (typeof message.status === 'string') status.value = message.status
    if (typeof message.max_players === 'number') maxPlayers.value = message.max_players
    if (Array.isArray(message.players)) players.value = parsePlayers(message.players)
    if (Array.isArray(message.topics)) topics.value = parseTopics(message.topics)
    if (typeof message.question_count === 'number') questionCount.value = message.question_count
  })

  realtime.on('match.started', (message) => {
    matchStarted.value = true
    status.value = 'question_active'
    if (typeof message.match_id === 'string') roomId.value = message.match_id
  })

  realtime.on('match.question', (message) => {
    if (!applyQuestionMessage(message)) error.value = 'INVALID_QUESTION'
  })

  realtime.on('match.standings', (message) => {
    if (Array.isArray(message.standings)) standings.value = parseStandings(message.standings)

    /* the server only names the right choice once the question is closed for
       everyone, so its arrival is what opens the reveal */
    if (typeof message.correct_choice_id === 'number') {
      correctChoice.value = message.correct_choice_id
      // a clock still ticking under a revealed answer reads like a bug
      stopCountdown()
    }

    if (
      typeof message.answered_by === 'number' &&
      !answeredBy.value.includes(message.answered_by)
    ) {
      answeredBy.value = [...answeredBy.value, message.answered_by]
    }
  })

  realtime.on('match.finished', applyFinished)

  realtime.on('match.state_sync', (message) => {
    if (typeof message.match_id !== 'string') return

    roomId.value = message.match_id
    if (typeof message.status === 'string') status.value = message.status
    if (typeof message.max_players === 'number') maxPlayers.value = message.max_players
    if (Array.isArray(message.players)) players.value = parsePlayers(message.players)
    if (Array.isArray(message.standings)) standings.value = parseStandings(message.standings)
    if (Array.isArray(message.topics)) topics.value = parseTopics(message.topics)
    if (typeof message.question_count === 'number') questionCount.value = message.question_count

    if (message.status === 'finished') {
      applyFinished(message)
    }

    if (isRecord(message.question)) {
      applyQuestionMessage({ ...message.question, remaining_seconds: message.remaining_seconds })
      if (typeof message.answered === 'boolean') answered.value = message.answered
      // after applyQuestionMessage, which clears the reveal of the round before
      if (typeof message.correct_choice_id === 'number') {
        correctChoice.value = message.correct_choice_id
        stopCountdown()
      }
    }
  })

  realtime.on('match.player_presence', (message) => {
    if (typeof message.user_id !== 'number' || typeof message.connected !== 'boolean') return

    players.value = players.value.map((player) =>
      player.id === message.user_id
        ? { ...player, connected: message.connected as boolean }
        : player,
    )
  })

  realtime.on('match.player_forfeit', (message) => {
    if (typeof message.user_id !== 'number') return

    players.value = players.value.filter((player) => player.id !== message.user_id)
    standings.value = standings.value.filter((standing) => standing.userId !== message.user_id)
  })

  realtime.on('error', (message) => {
    if (typeof message.code !== 'string' || !message.code.length) return
    // a stale answer is harmless: the next question is already on its way
    if (message.code === 'ANSWER_TOO_LATE' || message.code === 'ALREADY_ANSWERED') return
    error.value = message.code
  })
}

export function useMultiplayer() {
  const realtime = useRealtime()
  listen()

  const connected = computed(() => realtime.status.value === 'online')

  const phase = computed<MatchPhase>(() => {
    if (roomId.value === null) return 'setup'
    if (finished.value) return 'finished'
    if (matchStarted.value) return 'playing'
    return 'lobby'
  })

  const ranking = computed(() => {
    // no standings until the first answer: everyone starts at 0
    const board = standings.value.length
      ? standings.value
      : players.value.map((player) => ({
          userId: player.id,
          displayName: player.displayName,
          avatarPath: player.avatarPath,
          score: 0,
        }))
    return [...board].sort((a, b) => b.score - a.score)
  })

  /* a normal finish carries no winner_id: the top score wins */
  const winner = computed(() => {
    const id = winnerId.value ?? ranking.value[0]?.userId ?? null
    return ranking.value.find((standing) => standing.userId === id) ?? null
  })

  function reconnect() {
    realtime.reconnect()
  }

  function clearError() {
    error.value = null
  }

  function createRoom(size = 4, topicsArray: string[] = [], count = 10) {
    error.value = null
    realtime.send({
      type: 'match.create',
      max_players: size,
      topics: topicsArray,
      question_count: count,
    })
  }

  function joinRoom(matchId: string) {
    error.value = null
    realtime.send({ type: 'match.join', match_id: matchId.trim().toUpperCase() })
  }

  function setReady(ready: boolean) {
    if (roomId.value === null) {
      error.value = 'NOT_IN_MATCH'
      return
    }

    realtime.send({ type: 'match.ready', match_id: roomId.value, ready })
  }

  function answer(choiceId: number) {
    if (roomId.value === null || question.value === null || answered.value) return

    answered.value = true
    pickedChoice.value = choiceId
    realtime.send({
      type: 'match.answer',
      match_id: roomId.value,
      question_id: question.value.id,
      choice_id: choiceId,
    })
  }

  function leaveRoom() {
    if (roomId.value !== null) {
      realtime.send({ type: 'match.leave', match_id: roomId.value })
    }
    resetMatch()
  }

  return {
    connected,
    phase,
    roomId: readonly(roomId),
    maxPlayers: readonly(maxPlayers),
    players,
    status: readonly(status),
    error: readonly(error),
    question,
    answered: readonly(answered),
    pickedChoice: readonly(pickedChoice),
    correctChoice: readonly(correctChoice),
    answeredBy,
    ranking,
    finishReason: readonly(finishReason),
    winner,
    remainingSeconds: readonly(remainingSeconds),
    topics: readonly(topics),
    questionCount: readonly(questionCount),
    reconnect,
    clearError,
    createRoom,
    joinRoom,
    setReady,
    answer,
    leaveRoom,
  }
}
