<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { t } = useI18n()
const { login, verifyTotp } = useAuth()

const email = ref('')
const password = ref('')
const totpCode = ref('')

const step = ref<'credentials' | 'totp'>('credentials')
const error = ref('')
const busy = ref(false)

function messageFor(err: unknown): string {
  const status = httpStatus(err)
  if (status === 429) return t('auth.errors.tooMany')
  if (step.value === 'totp') {
    if (status === 400 || status === 422) return t('auth.errors.invalidCode')
    if (status === 401) return t('auth.errors.mfaExpired')
  }
  if (status === 401) return t('auth.errors.invalidLogin')
  if (status === 422) {
    return invalidField(err) === 'email'
      ? t('auth.errors.invalidEmail')
      : t('auth.errors.invalidInput')
  }
  return t('auth.errors.generic')
}

async function submitCredentials() {
  busy.value = true
  error.value = ''
  try {
    const { mfaRequired } = await login(email.value, password.value)
    if (mfaRequired) {
      step.value = 'totp'
    } else {
      await navigateTo('/dashboard')
    }
  } catch (err) {
    error.value = messageFor(err)
  } finally {
    busy.value = false
  }
}

async function submitTotp() {
  busy.value = true
  error.value = ''
  try {
    await verifyTotp(totpCode.value)
    await navigateTo('/dashboard')
  } catch (err) {
    error.value = messageFor(err)
    // the 2FA step expired: its token is gone, only a new password step helps
    if (httpStatus(err) === 401) {
      step.value = 'credentials'
      totpCode.value = ''
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AuthShell
    :title="$t('auth.loginTitle')"
    :subtitle="$t('auth.loginSubtitle')"
    :alt-label="$t('auth.signUp')"
    alt-to="/sign-up"
  >
    <UiCallout v-if="error" tone="danger" icon="lucide:circle-alert" class="mb-4">
      {{ error }}
    </UiCallout>

    <form v-if="step === 'credentials'" class="space-y-4" @submit.prevent="submitCredentials">
      <div>
        <label for="login-email" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.email') }}
        </label>
        <UiInput
          id="login-email"
          v-model="email"
          type="email"
          required
          autocomplete="email"
          :placeholder="$t('auth.emailPlaceholder')"
        />
      </div>
      <div>
        <label for="login-password" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.password') }}
        </label>
        <UiInput
          id="login-password"
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          :placeholder="$t('auth.passwordPlaceholder')"
        />
      </div>
      <UiButton
        type="submit"
        block
        size="lg"
        :label="busy ? $t('auth.signingIn') : $t('auth.signIn')"
      />
    </form>

    <form v-else class="space-y-4" @submit.prevent="submitTotp">
      <p class="text-sm text-fg-muted">{{ $t('auth.totpPrompt') }}</p>
      <div>
        <label for="login-totp" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.totpCode') }}
        </label>
        <UiInput
          id="login-totp"
          v-model="totpCode"
          type="text"
          required
          inputmode="numeric"
          autocomplete="one-time-code"
          placeholder="123456"
        />
      </div>
      <UiButton type="submit" block size="lg" :label="$t('auth.verify')" />
    </form>

    <template v-if="step === 'credentials'">
      <AuthDivider />
      <AuthProviders mode="login" />
      <p class="mt-4 text-center text-xs text-fg-subtle">
        <NuxtLink
          to="/forgotten-password"
          class="rounded-xs transition-colors duration-fast hover:text-fg-body focus-visible:shadow-focus focus-visible:outline-none"
        >
          {{ $t('auth.forgotPassword') }}
        </NuxtLink>
      </p>
    </template>
  </AuthShell>
</template>
