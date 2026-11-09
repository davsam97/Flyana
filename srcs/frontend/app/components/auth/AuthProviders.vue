<script setup lang="ts">
const { t } = useI18n()

const { mode } = defineProps<{
  mode: 'login' | 'signup'
}>()

const getLabel = (provider: string) => {
  if (mode === 'login') {
    return t('auth.providers.continueWith', { provider })
  }
  return t('auth.providers.signUpWith', { provider })
}

const startAuth = (provider: string) => {
  window.location.href = `/api/v1/auth/oauth/${provider}/authorize`
}

const PROVIDER_BUTTON =
  'flex h-11.5 flex-1 items-center justify-center rounded-md border border-line-strong bg-surface-raised text-fg-body transition-colors duration-fast hover:bg-surface-hover focus-visible:shadow-focus focus-visible:outline-none'
</script>

<template>
  <div>
    <div class="flex gap-2.5">
      <button
        :class="PROVIDER_BUTTON"
        :aria-label="getLabel($t('auth.providers.github'))"
        @click="startAuth('github')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path
            d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.79 1.2 1.79 1.2 1.04 1.79 2.73 1.27 3.4.97.1-.76.41-1.27.74-1.56-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.24 2.76.12 3.05.74.81 1.19 1.84 1.19 3.1 0 4.43-2.7 5.4-5.26 5.69.42.36.79 1.08.79 2.18v3.23c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5Z"
          />
        </svg>
      </button>
      <button
        :class="PROVIDER_BUTTON"
        :aria-label="getLabel($t('auth.providers.google'))"
        @click="startAuth('google')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="#4285F4"
            d="M23.5 12.27c0-.79-.07-1.54-.2-2.27H12v4.51h6.47a5.53 5.53 0 0 1-2.4 3.63v3h3.88c2.27-2.09 3.55-5.17 3.55-8.87Z"
          />
          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.96-1.08 7.95-2.91l-3.88-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.26v3.09A12 12 0 0 0 12 24Z"
          />
          <path
            fill="#FBBC05"
            d="M5.27 14.28a7.2 7.2 0 0 1 0-4.56V6.63H1.26a12 12 0 0 0 0 10.74l4.01-3.09Z"
          />
          <path
            fill="#EA4335"
            d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.44-3.44A12 12 0 0 0 12 0 12 12 0 0 0 1.26 6.63l4.01 3.09C6.22 6.86 8.87 4.75 12 4.75Z"
          />
        </svg>
      </button>
      <button
        :class="PROVIDER_BUTTON"
        :aria-label="getLabel($t('auth.providers.intra42'))"
        @click="startAuth('fortytwo')"
      >
        <svg width="18" height="18" viewBox="0 0 204 192" fill="currentColor" aria-hidden="true">
          <g transform="translate(0,192) scale(0.1,-0.1)" stroke="none">
            <path
              d="M417 1312 l-347 -347 0 -143 0 -142 350 0 350 0 0 -175 0 -175 175 0 175 0 0 315 0 315 -345 0 c-190 0 -345 3 -345 7 0 5 154 162 342 350 l343 343 -175 0 -175 0 -348 -348z"
            />
            <path
              d="M1270 1488 l0 -173 170 170 c94 93 170 171 170 172 0 2 -76 3 -170 3 l-170 0 0 -172z"
            />
            <path
              d="M1620 1488 l-1 -173 -174 -178 -175 -179 0 -174 0 -174 350 0 350 0 0 172 0 173 -168 -168 c-92 -92 -171 -167 -175 -167 -4 0 -7 78 -7 173 l0 172 175 175 175 175 0 172 0 173 -175 0 -175 0 0 -172z"
            />
          </g>
        </svg>
      </button>
    </div>
    <!-- OAuth can create an account from either page: accepting is implicit here -->
    <i18n-t keypath="auth.oauthTerms" tag="p" class="mt-4 text-center text-xs text-fg-subtle">
      <template #terms>
        <NuxtLink to="/terms" target="_blank" class="underline hover:text-fg-body">
          {{ $t('auth.termsLink') }}
        </NuxtLink>
      </template>
      <template #privacy>
        <NuxtLink to="/privacy" target="_blank" class="underline hover:text-fg-body">
          {{ $t('auth.privacyLink') }}
        </NuxtLink>
      </template>
    </i18n-t>
  </div>
</template>
