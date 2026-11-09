<script setup lang="ts">
definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { t } = useI18n()
const { user, fetchMe, updateProfile, uploadAvatar, logout, deleteAccount } = useAuth()
const { api } = useApi()

await fetchMe()

function detail(err: unknown, fallback: string): string {
  return t(apiErrorKey(err) ?? fallback)
}

const form = reactive({
  display_name: user.value?.display_name ?? '',
  bio: user.value?.bio ?? '',
})
const profileMsg = ref('')
const profileErr = ref('')
const savingProfile = ref(false)

async function saveProfile() {
  savingProfile.value = true
  profileMsg.value = ''
  profileErr.value = ''
  try {
    await updateProfile({
      display_name: form.display_name,
      bio: form.bio,
    })
    profileMsg.value = t('settings.saved')
  } catch (err) {
    profileErr.value = detail(err, 'settings.saveError')
  } finally {
    savingProfile.value = false
  }
}

const avatarErr = ref('')
const uploadingAvatar = ref(false)
const avatarSrc = computed(() => user.value?.avatar_path ?? null)

async function onAvatarPick(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingAvatar.value = true
  avatarErr.value = ''
  try {
    await uploadAvatar(file)
  } catch (err) {
    const status = httpStatus(err)
    if (status === 413 || status === 415) {
      avatarErr.value = t('settings.avatarRejected')
    } else {
      avatarErr.value = detail(err, 'settings.saveError')
    }
  } finally {
    uploadingAvatar.value = false
    ;(event.target as HTMLInputElement).value = ''
  }
}

type Setup = { otpauth_uri: string; qr_code_png_base64: string }
const twoFa = reactive({
  stage: 'idle' as 'idle' | 'enrolling' | 'done',
  qr: '',
  code: '',
  password: '',
  backupCodes: [] as string[],
  error: '',
  busy: false,
})

async function startEnroll() {
  twoFa.busy = true
  twoFa.error = ''
  try {
    const s = await api<Setup>('/api/v1/auth/2fa/setup', { method: 'POST' })
    twoFa.qr = `data:image/png;base64,${s.qr_code_png_base64}`
    twoFa.stage = 'enrolling'
  } catch (err) {
    twoFa.error = detail(err, 'settings.saveError')
  } finally {
    twoFa.busy = false
  }
}

async function confirmEnroll() {
  twoFa.busy = true
  twoFa.error = ''
  try {
    const r = await api<{ backup_codes: string[] }>('/api/v1/auth/2fa/enable', {
      method: 'POST',
      body: { code: twoFa.code },
    })
    twoFa.backupCodes = r.backup_codes
    twoFa.stage = 'done'
    twoFa.code = ''
    await fetchMe(true)
  } catch (err) {
    twoFa.error = detail(err, 'settings.twoFaBadCode')
  } finally {
    twoFa.busy = false
  }
}

async function disableTwoFa() {
  twoFa.busy = true
  twoFa.error = ''
  try {
    await api('/api/v1/auth/2fa', {
      method: 'DELETE',
      body: { password: twoFa.password, code: twoFa.code },
    })
    twoFa.password = ''
    twoFa.code = ''
    twoFa.stage = 'idle'
    await fetchMe(true)
  } catch (err) {
    twoFa.error = detail(err, 'settings.twoFaBadCode')
  } finally {
    twoFa.busy = false
  }
}

const removal = reactive({
  open: false,
  confirmation: '',
  password: '',
  error: '',
  busy: false,
})

const canDelete = computed(
  () =>
    !removal.busy &&
    removal.confirmation === user.value?.display_name &&
    (!user.value?.has_password || removal.password.length > 0),
)

function cancelDelete() {
  removal.open = false
  removal.confirmation = ''
  removal.password = ''
  removal.error = ''
}

async function confirmDelete() {
  if (!canDelete.value) return
  removal.busy = true
  removal.error = ''
  try {
    await deleteAccount({
      confirmation: removal.confirmation,
      ...(user.value?.has_password ? { password: removal.password } : {}),
    })
  } catch (err) {
    removal.error = detail(err, 'settings.deleteError')
  } finally {
    removal.busy = false
  }
}
</script>

<template>
  <div v-if="user" class="mx-auto w-full max-w-160 space-y-6">
    <h1 class="flex items-center gap-2 text-2xl font-semibold">
      <Icon name="lucide:settings" mode="svg" size="1em" class="text-accent" aria-hidden="true" />
      {{ $t('nav.settings') }}
    </h1>

    <UiCard pad>
      <h2 class="mb-3 text-sm font-semibold">{{ $t('settings.avatar') }}</h2>
      <div class="flex flex-wrap items-center gap-4">
        <UiAvatar :name="user.display_name" :src="avatarSrc" :size="64" ring />
        <label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            class="hidden"
            @change="onAvatarPick"
          />
          <span
            class="inline-flex h-7 cursor-pointer items-center rounded-md border border-line-strong bg-surface-raised px-4 text-sm font-semibold hover:bg-surface-hover"
          >
            {{ uploadingAvatar ? $t('settings.uploading') : $t('settings.chooseImage') }}
          </span>
        </label>
      </div>
      <UiCallout v-if="avatarErr" tone="danger" class="mt-3">{{ avatarErr }}</UiCallout>
    </UiCard>

    <UiCard pad>
      <h2 class="mb-3 text-sm font-semibold">{{ $t('settings.profile') }}</h2>
      <form class="space-y-4" @submit.prevent="saveProfile">
        <div>
          <label for="set-name" class="mb-1.5 block text-sm font-semibold">
            {{ $t('auth.username') }}
          </label>
          <UiInput
            id="set-name"
            v-model="form.display_name"
            type="text"
            required
            pattern="[A-Za-z0-9_-]{3,24}"
          />
        </div>
        <div>
          <label for="set-bio" class="mb-1.5 block text-sm font-semibold">
            {{ $t('settings.bio') }}
          </label>
          <UiTextarea id="set-bio" v-model="form.bio" maxlength="500" />
        </div>
        <UiButton
          type="submit"
          :label="savingProfile ? $t('settings.saving') : $t('settings.save')"
        />
        <UiCallout v-if="profileMsg" tone="success" class="mt-1">{{ profileMsg }}</UiCallout>
        <UiCallout v-if="profileErr" tone="danger" class="mt-1">{{ profileErr }}</UiCallout>
      </form>
    </UiCard>

    <UiCard pad>
      <h2 class="mb-1 text-sm font-semibold">{{ $t('settings.twoFa') }}</h2>
      <p class="mb-3 text-xs text-fg-subtle">{{ $t('settings.twoFaHint') }}</p>

      <template v-if="!user.totp_enabled || twoFa.stage === 'done'">
        <UiButton
          v-if="twoFa.stage === 'idle'"
          :label="$t('settings.twoFaEnable')"
          :disabled="twoFa.busy"
          @click="startEnroll"
        />

        <div v-else-if="twoFa.stage === 'enrolling'" class="space-y-3">
          <img
            :src="twoFa.qr"
            alt=""
            class="size-44 rounded-md border border-line-subtle bg-white p-2"
          />
          <p class="text-xs text-fg-subtle">{{ $t('settings.twoFaScan') }}</p>
          <UiInput v-model="twoFa.code" type="text" inputmode="numeric" placeholder="123456" />
          <UiButton
            :label="$t('settings.twoFaConfirm')"
            :disabled="twoFa.busy"
            @click="confirmEnroll"
          />
        </div>

        <div v-else class="space-y-2">
          <UiCallout tone="success" icon="lucide:circle-check">
            {{ $t('settings.twoFaDone') }}
          </UiCallout>
          <p class="text-xs font-semibold">{{ $t('settings.backupCodes') }}</p>
          <ul class="grid grid-cols-2 gap-1 font-mono text-sm">
            <li v-for="c in twoFa.backupCodes" :key="c">{{ c }}</li>
          </ul>
        </div>
      </template>

      <div v-else class="space-y-3">
        <UiCallout tone="success" icon="lucide:shield-check">{{
          $t('settings.twoFaOn')
        }}</UiCallout>
        <UiInput v-model="twoFa.password" type="password" :placeholder="$t('auth.password')" />
        <UiInput v-model="twoFa.code" type="text" inputmode="numeric" placeholder="123456" />
        <UiButton
          variant="secondary"
          :label="$t('settings.twoFaDisable')"
          :disabled="twoFa.busy"
          @click="disableTwoFa"
        />
      </div>

      <UiCallout v-if="twoFa.error" tone="danger" class="mt-3">{{ twoFa.error }}</UiCallout>
    </UiCard>

    <UiCard pad>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <h2 class="text-sm font-semibold">{{ $t('settings.session') }}</h2>
          <p class="text-xs break-all text-fg-subtle">{{ user.email }}</p>
        </div>
        <UiButton variant="secondary" :label="$t('settings.logout')" @click="logout" />
      </div>
    </UiCard>

    <UiCard pad class="border-danger">
      <h2 class="mb-1 text-sm font-semibold text-danger">{{ $t('settings.deleteTitle') }}</h2>
      <p class="mb-3 text-xs text-fg-subtle">{{ $t('settings.deleteHint') }}</p>

      <UiButton
        v-if="!removal.open"
        variant="danger"
        :label="$t('settings.deleteAccount')"
        @click="removal.open = true"
      >
        <Icon name="lucide:trash-2" mode="svg" size="1em" />
      </UiButton>

      <form v-else class="space-y-3" @submit.prevent="confirmDelete">
        <UiCallout tone="danger" icon="lucide:triangle-alert">
          {{ $t('settings.deleteWarning') }}
        </UiCallout>
        <div>
          <label for="del-confirm" class="mb-1.5 block text-sm font-semibold">
            {{ $t('settings.deleteConfirmLabel', { name: user.display_name }) }}
          </label>
          <UiInput
            id="del-confirm"
            v-model="removal.confirmation"
            type="text"
            autocomplete="off"
            spellcheck="false"
            :placeholder="user.display_name"
          />
        </div>
        <div v-if="user.has_password">
          <label for="del-password" class="mb-1.5 block text-sm font-semibold">
            {{ $t('auth.password') }}
          </label>
          <UiInput
            id="del-password"
            v-model="removal.password"
            type="password"
            autocomplete="current-password"
          />
        </div>
        <div class="flex flex-wrap gap-2">
          <UiButton
            type="submit"
            variant="danger"
            :label="removal.busy ? $t('settings.deleting') : $t('settings.deleteForever')"
            :disabled="!canDelete"
          />
          <UiButton
            variant="ghost"
            :label="$t('settings.deleteCancel')"
            :disabled="removal.busy"
            @click="cancelDelete"
          />
        </div>
        <UiCallout v-if="removal.error" tone="danger">{{ removal.error }}</UiCallout>
      </form>
    </UiCard>
  </div>
</template>
