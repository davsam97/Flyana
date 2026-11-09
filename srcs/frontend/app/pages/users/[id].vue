<script setup lang="ts">
import type { Profile } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { t } = useI18n()
const { api } = useApi()
const route = useRoute()
const userId = computed(() => Number(route.params.id))

const profile = ref<Profile | null>(null)
const notFound = ref(false)
const actionError = ref('')

const { sendRequest, accept, remove, block, unblock } = useFriends()

async function load() {
  notFound.value = false
  try {
    profile.value = await api<Profile>(`/api/v1/users/${userId.value}`)
  } catch {
    notFound.value = true
  }
}

watch(userId, load, { immediate: true })

const joined = computed(() =>
  profile.value ? new Date(profile.value.created_at).toLocaleDateString() : '',
)

async function guard(fn: () => Promise<unknown>) {
  actionError.value = ''
  try {
    await fn()
    await load()
  } catch (err) {
    actionError.value = t(apiErrorKey(err) ?? 'friends.errGeneric')
  }
}

const addFriend = () => guard(() => sendRequest(userId.value))
const blockUser = () => guard(() => block(userId.value))
const liftBlock = () => guard(() => unblock(userId.value))
const acceptFriend = () =>
  guard(async () => {
    const id = profile.value?.friendship_id
    if (id) await accept(id)
  })
const dropRelation = () =>
  guard(async () => {
    const id = profile.value?.friendship_id
    if (id) await remove(id)
  })
</script>

<template>
  <div class="mx-auto w-full max-w-160 space-y-4">
    <p v-if="notFound" class="text-sm text-fg-subtle">{{ $t('profile.notFound') }}</p>

    <template v-else-if="profile">
      <UiCallout v-if="actionError" tone="danger" icon="lucide:circle-alert">
        {{ actionError }}
      </UiCallout>

      <UiCard pad>
        <div class="flex items-start gap-4">
          <UiAvatar :name="profile.display_name" :src="profile.avatar_path" :size="64" ring />
          <div class="min-w-0 flex-1">
            <h1 class="text-xl font-semibold break-words">{{ profile.display_name }}</h1>
            <UiPresenceDot :user-id="profile.id" label />
            <p class="mt-1 text-xs text-fg-subtle">
              {{ $t('profile.joined', { date: joined }) }}
            </p>
          </div>
        </div>

        <p v-if="profile.bio" class="mt-4 text-sm break-words text-fg-body">{{ profile.bio }}</p>
        <p v-else class="mt-4 text-sm text-fg-subtle">{{ $t('profile.noBio') }}</p>

        <div class="mt-5 flex flex-wrap gap-2">
          <template v-if="profile.friendship === 'friends'">
            <NuxtLink :to="{ path: '/messages', query: { to: profile.id } }">
              <UiButton :label="$t('friends.message')" />
            </NuxtLink>
            <UiButton variant="ghost" :label="$t('friends.remove')" @click="dropRelation" />
            <UiButton variant="ghost" :label="$t('friends.block')" @click="blockUser" />
          </template>

          <template v-else-if="profile.friendship === 'none'">
            <UiButton :label="$t('friends.add')" @click="addFriend" />
            <UiButton variant="ghost" :label="$t('friends.block')" @click="blockUser" />
          </template>

          <template v-else-if="profile.friendship === 'pending_in'">
            <UiButton :label="$t('friends.accept')" @click="acceptFriend" />
            <UiButton variant="ghost" :label="$t('friends.decline')" @click="dropRelation" />
          </template>

          <template v-else-if="profile.friendship === 'pending_out'">
            <span class="self-center text-xs text-fg-subtle">{{ $t('friends.pending') }}</span>
            <UiButton variant="ghost" :label="$t('friends.cancel')" @click="dropRelation" />
          </template>

          <UiButton
            v-else-if="profile.friendship === 'blocked'"
            variant="secondary"
            :label="$t('profile.unblock')"
            @click="liftBlock"
          />
        </div>
      </UiCard>
    </template>
  </div>
</template>
