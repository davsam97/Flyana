export default defineNuxtPlugin(() => {
  const rawFetch = $fetch.create({
    baseURL: '/api/v1',
    credentials: 'include',
    onRequest({ options }) {
      const method = (options.method ?? 'GET').toUpperCase()
      if (method === 'GET' || method === 'HEAD') return
      const csrfToken = useCookie<string | null>('csrf_token')
      if (!csrfToken.value) return
      const headers = new Headers(options.headers)
      headers.set('X-CSRF-Token', csrfToken.value)
      options.headers = headers
    },
  })
  let refreshPromise: Promise<void> | null = null

  function ensureFreshSession(): Promise<void> {
    if (refreshPromise != null) return refreshPromise
    else
      refreshPromise = rawFetch('/auth/refresh', { method: 'POST' })
        .then(() => {})
        .finally(() => (refreshPromise = null))
    return refreshPromise
  }

  type ApiOptions = NonNullable<Parameters<typeof rawFetch>[1]> & { _retried?: boolean }

  async function apiFetch<T = unknown>(request: string, options: ApiOptions = {}): Promise<T> {
    try {
      return await rawFetch<T>(request, options)
    } catch (err) {
      if (
        httpStatus(err) === 401 &&
        !options._retried &&
        request !== '/auth/login' &&
        request !== '/auth/refresh'
      ) {
        await ensureFreshSession()
        return apiFetch<T>(request, { ...options, _retried: true })
      } else throw err
    }
  }

  return {
    provide: { api: apiFetch },
  }
})
