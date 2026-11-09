<script setup lang="ts">
import { validateDisplayName, validatePassword } from '#shared/validation'

definePageMeta({ layout: 'default' })

const { t } = useI18n()
const { register } = useAuth()

const draftUser = ref('')
const draftEmail = ref('')
const draftPass = ref('')
const draftConfirm = ref('')
const acceptTerms = ref(false)

const passwordInput = ref<{ el?: HTMLInputElement }>()
const confirmInput = ref<{ el?: HTMLInputElement }>()
const displayNameInput = ref<{ el?: HTMLInputElement }>()
const formInput = ref<HTMLFormElement>()

const error = ref('')
const busy = ref(false)

// mirrors COMMON_PASSWORDS in the backend schema — fast feedback before the 422
const WEAK_PASSWORDS = new Set([
  'password12',
  'password123',
  '1234567890',
  'qwertyuiop',
  'azertyuiop',
  'motdepasse',
  'administrator',
  'abc12345678',
])

function checkDisplayName(): boolean {
  const displayName = displayNameInput.value?.el

  if (!displayName) return false

  const message = validateDisplayName(draftUser.value)
  if (message !== null) {
    displayName.setCustomValidity(t(`auth.errors.${message}`))
    return false
  }
  displayName.setCustomValidity('')
  return true
}

function checkPassword(): boolean {
  const password = passwordInput.value?.el
  const confirm = confirmInput.value?.el
  if (!password || !confirm) return false

  password.setCustomValidity('')
  confirm.setCustomValidity('')

  const message = validatePassword(draftPass.value, draftEmail.value)
  if (message !== null) {
    password.setCustomValidity(t(`auth.errors.${message}`))
    return false
  }
  if (WEAK_PASSWORDS.has(draftPass.value.toLowerCase())) {
    password.setCustomValidity(t('auth.errors.passwordWeak'))
    return false
  }
  if (draftPass.value !== draftConfirm.value && draftConfirm.value.length > 0) {
    confirm.setCustomValidity(t('auth.errors.passwordMismatch'))
    return false
  }
  return true
}

function messageFor(err: unknown): string {
  const status = httpStatus(err)
  const detail = httpDetail(err)
  if (status === 409 && detail) {
    if (detail.includes('email')) return t('auth.errors.emailTaken')
    if (detail.includes('display')) return t('auth.errors.nameTaken')
  }
  if (status === 429) return t('auth.errors.tooMany')
  if (status === 422) {
    const field = invalidField(err)
    if (field === 'email') return t('auth.errors.invalidEmail')
    if (field === 'display_name') return t('auth.errors.displayNameInvalid')
    if (field === 'password') return t('auth.errors.passwordWeak')
    return t('auth.errors.invalidInput')
  }
  return t('auth.errors.generic')
}

async function checkForm() {
  if (!checkPassword() || !checkDisplayName()) {
    formInput.value?.reportValidity()
    return
  }
  busy.value = true
  error.value = ''
  try {
    await register({
      email: draftEmail.value,
      password: draftPass.value,
      displayName: draftUser.value,
      acceptTerms: acceptTerms.value,
    })
    await navigateTo('/dashboard')
  } catch (err) {
    error.value = messageFor(err)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AuthShell
    :title="$t('auth.signupTitle')"
    :subtitle="$t('auth.signupSubtitle')"
    :alt-label="$t('auth.signIn')"
    alt-to="/login"
  >
    <UiCallout v-if="error" tone="danger" icon="lucide:circle-alert" class="mb-4">
      {{ error }}
    </UiCallout>

    <form ref="formInput" class="space-y-4" @submit.prevent="checkForm">
      <div>
        <label for="signup-login42" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.username') }}
        </label>
        <UiInput
          id="signup-login42"
          ref="displayNameInput"
          v-model="draftUser"
          type="text"
          required
          autocomplete="username"
          pattern="[A-Za-z0-9_\-]{3,24}"
          :placeholder="$t('auth.login42Placeholder')"
          @keyup="checkDisplayName"
        />
      </div>
      <div>
        <label for="signup-email" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.email') }}
        </label>
        <UiInput
          id="signup-email"
          v-model="draftEmail"
          type="email"
          required
          autocomplete="email"
          :placeholder="$t('auth.emailPlaceholder')"
        />
      </div>
      <div>
        <label for="signup-password" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.password') }}
        </label>
        <UiInput
          id="signup-password"
          ref="passwordInput"
          v-model="draftPass"
          type="password"
          required
          autocomplete="new-password"
          :placeholder="$t('auth.passwordPlaceholder')"
          aria-describedby="signup-password-hint"
          @keyup="checkPassword"
        />
        <p id="signup-password-hint" class="mt-1.5 text-xs text-fg-subtle">
          {{ $t('auth.passwordHint') }}
        </p>
      </div>
      <div>
        <label for="signup-confirm" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.passwordConfirm') }}
        </label>
        <UiInput
          id="signup-confirm"
          ref="confirmInput"
          v-model="draftConfirm"
          type="password"
          required
          autocomplete="new-password"
          :placeholder="$t('auth.passwordPlaceholder')"
          @keyup="checkPassword"
        />
      </div>
      <label for="signup-terms" class="flex items-start gap-2.5 text-sm text-fg-muted">
        <input
          id="signup-terms"
          v-model="acceptTerms"
          type="checkbox"
          required
          class="mt-0.5 size-4 flex-none accent-accent"
        />
        <i18n-t keypath="auth.acceptTerms" tag="span">
          <template #terms>
            <NuxtLink to="/terms" target="_blank" class="text-accent underline">
              {{ $t('auth.termsLink') }}
            </NuxtLink>
          </template>
          <template #privacy>
            <NuxtLink to="/privacy" target="_blank" class="text-accent underline">
              {{ $t('auth.privacyLink') }}
            </NuxtLink>
          </template>
        </i18n-t>
      </label>
      <UiButton
        type="submit"
        block
        size="lg"
        :label="busy ? $t('auth.creating') : $t('auth.createAccount')"
      />
    </form>

    <AuthDivider />

    <AuthProviders mode="signup" />
  </AuthShell>
</template>
