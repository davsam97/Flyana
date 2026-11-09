<script setup lang="ts">
definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { user, fetchMe } = useAuth()
const { friends, refresh } = useFriends()

await fetchMe()
onMounted(refresh)

const avatarSrc = computed(() => user.value?.avatar_path ?? null)
const joined = computed(() =>
  user.value ? new Date(user.value.created_at).toLocaleDateString() : '',
)
</script>

<template>
  <div v-if="user" class="mx-auto w-full max-w-160 space-y-5">
    <div class="flex items-start justify-between gap-4">
      <h1 class="text-2xl font-semibold">{{ $t('nav.profil') }}</h1>
      <NuxtLink to="/settings">
        <UiButton size="sm" variant="secondary" :label="$t('profile.edit')">
          <template #trailing><Icon name="lucide:settings" mode="svg" size="1em" /></template>
        </UiButton>
      </NuxtLink>
    </div>

    <UiCard pad>
      <div class="flex items-start gap-4">
        <UiAvatar :name="user.display_name" :src="avatarSrc" :size="72" ring />
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-xl font-semibold break-words">{{ user.display_name }}</h2>
            <UiChip :label="$t(`roles.${user.role}`)" />
          </div>
          <p class="text-sm break-all text-fg-subtle">{{ user.email }}</p>
          <p class="mt-1 text-xs text-fg-subtle">{{ $t('profile.joined', { date: joined }) }}</p>
        </div>
      </div>

      <p v-if="user.bio" class="mt-4 text-sm break-words text-fg-body">{{ user.bio }}</p>
      <p v-else class="mt-4 text-sm text-fg-subtle">{{ $t('profile.noBio') }}</p>
    </UiCard>

    <div class="grid gap-4 sm:grid-cols-3">
      <UiCard pad>
        <UiStat :value="friends.length" :label="$t('nav.friends')" />
      </UiCard>
      <UiCard pad>
        <p class="text-xs text-fg-subtle">{{ $t('settings.twoFa') }}</p>
        <p class="mt-1 text-sm font-semibold" :class="user.totp_enabled ? 'text-success' : ''">
          {{ user.totp_enabled ? $t('settings.twoFaOn') : $t('settings.twoFaOff') }}
        </p>
      </UiCard>
      <UiCard pad>
        <p class="text-xs text-fg-subtle">{{ $t('profile.language') }}</p>
        <p class="mt-1 text-sm font-semibold uppercase">{{ user.locale }}</p>
      </UiCard>
    </div>

    <NuxtLink :to="`/users/${user.id}`" class="inline-block text-sm text-accent hover:underline">
      {{ $t('profile.viewPublic') }}
    </NuxtLink>
  </div>
</template>
