/* Keeps the access cookie fresh for as long as a private page is open.
 *
 * `attemptRefresh` elsewhere is reactive: something gets a 401, the session is
 * renewed, the call is retried. That is enough for a page that talks to the
 * API, and not enough for one that holds a websocket: the socket carries no
 * cookie once open, so a player can sit through a whole match looking active
 * while the access cookie lapses behind them. The first HTTP call afterwards —
 * the end-of-match recap — then 401s, and a socket that happens to drop can no
 * longer shake hands at all, since the handshake reads that same cookie.
 *
 * So the deadline is met rather than discovered: `access_expires_at`, set in
 * clear next to the HttpOnly token, says when, and the refresh is scheduled
 * just before it. State is module-scoped, like `useRealtime`: one session is
 * shared by every page that mounts.
 */

import { attemptRefresh, readCookie } from './useApi'

/* Refresh at least this long before the deadline, plus a random slice of
   SPREAD on top. The spread is not cosmetic: `/auth/refresh` rotates the
   refresh token and revokes the whole family if an already-rotated one comes
   back, so two tabs firing in the same instant could log the account out. A
   window this wide leaves the first refresh long finished — and its new cookie
   shared with every tab — before the second one fires. */
const MARGIN_MS = 60_000
const SPREAD_MS = 45_000
/* Never fire synchronously, even on an already-lapsed deadline: a refresh that
   fails would otherwise reschedule itself in a tight loop */
const MIN_DELAY_MS = 1_000

let timer: ReturnType<typeof setTimeout> | null = null
let watching = false

function clear() {
  if (timer !== null) {
    clearTimeout(timer)
    timer = null
  }
}

/* The deadline in epoch ms, or null when there is no readable session */
function deadline(): number | null {
  const raw = readCookie('access_expires_at')
  if (!raw) return null
  const seconds = Number(raw)
  return Number.isFinite(seconds) ? seconds * 1000 : null
}

function schedule() {
  clear()
  if (!watching) return

  const at = deadline()
  // no cookie: signed out, or a backend that predates it. The reactive refresh
  // on 401 stays in place either way, so there is nothing to fall back to
  if (at === null) return

  const advance = MARGIN_MS + Math.random() * SPREAD_MS
  const delay = Math.max(MIN_DELAY_MS, at - Date.now() - advance)
  timer = setTimeout(async () => {
    timer = null
    /* The cookie is shared by every tab, so it is also the only honest answer
       to "has someone already done this?". A deadline that moved while we
       waited means another tab refreshed — or any request did, reactively — and
       refreshing again on top of it is exactly the double rotation that gets
       the whole token family revoked. Reschedule on the new deadline instead. */
    if (deadline() !== at) {
      schedule()
      return
    }
    // a failed refresh means the session is really over: stop rather than
    // hammer `/auth/refresh`, and let the next 401 route the user to login
    if (await attemptRefresh()) schedule()
  }, delay)
}

/* Timers do not fire while a tab is asleep, and a laptop coming back from
   suspend can hold a cookie that lapsed hours ago. Re-reading the deadline on
   wake either reschedules or, past the deadline, refreshes almost at once */
function onVisibility() {
  if (document.visibilityState === 'visible') schedule()
}

export function useSession() {
  function start() {
    if (watching) return
    watching = true
    document.addEventListener('visibilitychange', onVisibility)
    schedule()
  }

  function stop() {
    watching = false
    document.removeEventListener('visibilitychange', onVisibility)
    clear()
  }

  return { start, stop }
}
