/* The signed-in account and every mutation that touches it (module-scoped state) */

import type { UserPublic } from '~/types/api.ts'

const user = ref<UserPublic | null>(null)
let inflight: Promise<UserPublic | null> | null = null

async function loadMe(): Promise<UserPublic | null> {
  try {
    user.value = await $fetch<UserPublic>('/api/v1/auth/me')
    return user.value
  } catch (err) {
    if (httpStatus(err) === 401 && (await attemptRefresh())) {
      try {
        user.value = await $fetch<UserPublic>('/api/v1/auth/me')
        return user.value
      } catch {
        /* refresh worked but /me still failed: treat as logged out */
      }
    }
    user.value = null
    return null
  }
}

export function useAuth() {
  const { api } = useApi()

  async function fetchMe(force = false): Promise<UserPublic | null> {
    if (user.value && !force) return user.value
    if (!inflight) {
      inflight = loadMe().finally(() => {
        inflight = null
      })
    }
    return inflight
  }

  /* Returns { mfaRequired } — when true the caller must collect a TOTP code
     and call `verifyTotp`; the session is not open yet. */
  async function login(email: string, password: string): Promise<{ mfaRequired: boolean }> {
    const res = await $fetch.raw('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    if (res.status === 202) return { mfaRequired: true }
    user.value = res._data as UserPublic
    return { mfaRequired: false }
  }

  async function verifyTotp(code: string): Promise<void> {
    user.value = await api<UserPublic>('/api/v1/auth/2fa/verify', {
      method: 'POST',
      body: { code },
    })
  }

  /* Register does not open a session server-side, so we log in right after. */
  async function register(input: {
    email: string
    password: string
    displayName: string
    acceptTerms: boolean
  }): Promise<{ mfaRequired: boolean }> {
    await $fetch('/api/v1/auth/register', {
      method: 'POST',
      body: {
        email: input.email,
        password: input.password,
        display_name: input.displayName,
        accept_terms: input.acceptTerms,
      },
    })
    return login(input.email, input.password)
  }

  async function logout(): Promise<void> {
    try {
      await api('/api/v1/auth/logout', { method: 'POST' })
    } finally {
      user.value = null
      await navigateTo('/login')
    }
  }

  /* Irreversible: the server drops the account and every row tied to it, then
     clears the auth cookies. */
  async function deleteAccount(body: { confirmation: string; password?: string }): Promise<void> {
    await api('/api/v1/users/me', { method: 'DELETE', body })
    user.value = null
    await navigateTo('/')
  }

  async function updateProfile(
    patch: Partial<Pick<UserPublic, 'display_name' | 'bio' | 'locale'>>,
  ) {
    user.value = await api<UserPublic>('/api/v1/users/me', { method: 'PATCH', body: patch })
  }

  async function uploadAvatar(file: File): Promise<void> {
    const form = new FormData()
    form.append('file', file)
    user.value = await api<UserPublic>('/api/v1/users/me/avatar', { method: 'POST', body: form })
  }

  return {
    user: readonly(user),
    fetchMe,
    login,
    verifyTotp,
    register,
    logout,
    deleteAccount,
    updateProfile,
    uploadAvatar,
  }
}
