/* Reading errors from `$fetch`, by shape rather than `instanceof FetchError`:
 * ofetch is not importable under pnpm's strict node_modules layout. */

export function httpStatus(err: unknown): number | undefined {
  const e = err as {
    status?: number
    statusCode?: number
    response?: { status?: number }
  }
  return e?.status ?? e?.statusCode ?? e?.response?.status
}

export function httpDetail(err: unknown): string | undefined {
  const d = (err as { data?: { detail?: unknown } })?.data?.detail
  return typeof d === 'string' ? d : undefined
}

/* FastAPI/pydantic 422: `detail` is a list of { loc, msg, ... }. Returns the
   field of the first error, so the page can show a translated message rather
   than pydantic's English text. */
export function invalidField(err: unknown): string | undefined {
  const d = (err as { data?: { detail?: unknown } })?.data?.detail
  if (!Array.isArray(d) || d.length === 0) return undefined
  const loc = (d[0] as { loc?: unknown })?.loc
  const field = Array.isArray(loc) ? loc[loc.length - 1] : undefined
  return typeof field === 'string' ? field : undefined
}

/* The API answers in English (`detail`), whatever the interface language.
   Maps each known detail to an i18n key under `apiErrors`, so a page never
   shows the server's text as is. Unknown details return undefined and the
   caller falls back to its own translated message. */
const API_ERROR_KEYS: Record<string, string> = {
  'name already taken': 'apiErrors.nameTaken',
  'invalid code': 'apiErrors.invalidCode',
  'call /2fa/setup first': 'apiErrors.twoFaSetupFirst',
  '2FA already enabled': 'apiErrors.twoFaAlreadyEnabled',
  '2FA not enabled': 'apiErrors.twoFaNotEnabled',
  'Invalid password': 'apiErrors.invalidPassword',
  'too many tries': 'apiErrors.tooMany',
  'invalid request': 'apiErrors.invalidRequest',
  unavailable: 'apiErrors.unavailable',
  'request already exists': 'apiErrors.requestExists',
  'already handled': 'apiErrors.alreadyHandled',
  blocked: 'apiErrors.blocked',
  'cannot be found': 'apiErrors.notFound',
  'user not found': 'apiErrors.notFound',
  'recipient not found': 'apiErrors.notFound',
  'invalid recipient': 'apiErrors.invalidRecipient',
  'slow down': 'apiErrors.slowDown',
  'unreadable image': 'apiErrors.imageUnreadable',
  'image too large once decoded': 'apiErrors.imageTooLarge',
  'confirmation mismatch': 'apiErrors.confirmationMismatch',
  'leave your match first': 'apiErrors.leaveMatchFirst',
}

export function apiErrorKey(err: unknown): string | undefined {
  const detail = httpDetail(err)
  if (detail !== undefined) {
    if (detail in API_ERROR_KEYS) return API_ERROR_KEYS[detail]
    // these two carry a variable part (size limit, detected format)
    if (detail.startsWith('file too heavy')) return 'apiErrors.fileTooHeavy'
    if (detail.startsWith('unauthorised format')) return 'apiErrors.imageFormat'
  }
  const status = httpStatus(err)
  // nginx answers an oversized upload itself, with an HTML body
  if (status === 413) return 'apiErrors.fileTooHeavy'
  if (status === 422) return 'apiErrors.invalidInput'
  if (status === 429) return 'apiErrors.tooMany'
  return undefined
}
