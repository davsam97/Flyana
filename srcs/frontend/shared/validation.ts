export const DISPLAY_NAME_RE = /^[a-zA-Z0-9_-]{3,24}$/

export const COMMON_PASSWORDS = new Set([
  'password12',
  'password123',
  '1234567890',
  'qwertyuiop',
  'azertyuiop',
  'motdepasse',
  'administrator',
  'abc12345678',
])

/* Returns an i18n key under `auth.errors`, like `validatePassword` */
export function validateDisplayName(value: string): string | null {
  if (!DISPLAY_NAME_RE.test(value)) return 'displayNameInvalid'
  return null
}

/* Returns an i18n key under `auth.errors`, mirroring the backend UserCreate
   validators so the user never waits for a 422. */
export function validatePassword(password: string, email: string): string | null {
  if (!(password.length >= 10 && password.length <= 128)) return 'passwordTooShort'
  if (COMMON_PASSWORDS.has(password.toLowerCase())) return 'passwordWeak'
  if (password.toLowerCase() === email.toLowerCase()) return 'passwordIsEmail'
  if (!/\p{Ll}/u.test(password)) return 'passwordNeedsLower'
  if (!/\p{Lu}/u.test(password)) return 'passwordNeedsUpper'
  if (!/\p{Nd}/u.test(password)) return 'passwordNeedsDigit'
  if (!/[^\p{L}\p{N}]/u.test(password)) return 'passwordNeedsSpecial'
  return null
}
