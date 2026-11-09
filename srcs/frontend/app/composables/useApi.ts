/* Same-origin fetch with the CSRF header and silent session refresh.
 *
 * The CSRF token is read from `document.cookie` on every call since each
 * login rotates it. A 401 outside `/auth/*` triggers one shared refresh, then
 * the request is retried.
 */

type ApiOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: Record<string, unknown> | FormData
  query?: Record<string, unknown>
  headers?: Record<string, string>
}

export function readCookie(name: string): string {
  const prefix = `${name}=`
  return (
    document.cookie
      .split('; ')
      .find((c) => c.startsWith(prefix))
      ?.slice(prefix.length) ?? ''
  )
}

export function csrfToken(): string {
  return readCookie('csrf_token')
}

// one refresh at a time, shared by every concurrent 401
let refreshing: Promise<boolean> | null = null

export function attemptRefresh(): Promise<boolean> {
  if (!refreshing) {
    refreshing = $fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken() },
    })
      .then(() => true)
      .catch(() => false)
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

export function useApi() {
  async function api<T>(url: string, opts: ApiOptions = {}): Promise<T> {
    const run = () => {
      const method = opts.method ?? 'GET'
      const headers: Record<string, string> = { ...opts.headers }
      if (method !== 'GET') headers['X-CSRF-Token'] = csrfToken()
      return $fetch<T>(url, { ...opts, headers })
    }
    try {
      return await run()
    } catch (err) {
      if (httpStatus(err) === 401 && !url.includes('/api/v1/auth/')) {
        if (await attemptRefresh()) return await run()
      }
      throw err
    }
  }

  return { api }
}
