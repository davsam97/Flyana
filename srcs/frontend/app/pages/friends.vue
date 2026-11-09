<script setup lang="ts">
import type { UserSummary } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const { t } = useI18n()
const { friends, incoming, outgoing, refresh, accept, remove, sendRequest, block, searchUsers } =
  useFriends()

const query = ref('')
const results = ref<UserSummary[]>([])
const searching = ref(false)
const actionError = ref('')

onMounted(refresh)

async function guard(fn: () => Promise<unknown>) {
  actionError.value = ''
  try {
    await fn()
  } catch (err) {
    const status = httpStatus(err)
    if (status === 409) actionError.value = t('friends.errConflict')
    else if (status === 429) actionError.value = t('auth.errors.tooMany')
    else actionError.value = t(apiErrorKey(err) ?? 'friends.errGeneric')
  }
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(query, (value) => {
  clearTimeout(searchTimer)
  const term = value.trim()
  if (term.length < 1) {
    results.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    searching.value = true
    try {
      results.value = await searchUsers(term)
    } catch {
      results.value = []
    } finally {
      searching.value = false
    }
  }, 250)
})

const knownIds = computed(
  () =>
    new Set([
      ...friends.value.map((f) => f.user.id),
      ...outgoing.value.map((r) => r.user.id),
      ...incoming.value.map((r) => r.user.id),
    ]),
)
</script>

<template>
  <div class="mx-auto w-full max-w-200 space-y-6">
    <h1 class="text-2xl font-semibold">{{ $t('nav.friends') }}</h1>

    <UiCallout v-if="actionError" tone="danger" icon="lucide:circle-alert">
      {{ actionError }}
    </UiCallout>

    <UiCard pad>
      <p class="mb-2 text-sm font-semibold">{{ $t('friends.find') }}</p>
      <UiInput
        v-model="query"
        type="search"
        icon="lucide:search"
        :placeholder="$t('friends.searchPlaceholder')"
      />
      <ul v-if="results.length" class="mt-3 divide-y divide-line-subtle">
        <li
          v-for="person in results"
          :key="person.id"
          class="flex flex-wrap items-center gap-x-3 gap-y-2 py-2"
        >
          <UiAvatar :name="person.display_name" :size="32" />
          <NuxtLink
            :to="`/users/${person.id}`"
            class="min-w-32 flex-1 truncate text-sm font-medium hover:underline"
          >
            {{ person.display_name }}
          </NuxtLink>
          <UiButton
            v-if="!knownIds.has(person.id)"
            size="sm"
            variant="secondary"
            class="ml-auto"
            :label="$t('friends.add')"
            @click="guard(() => sendRequest(person.id))"
          />
          <span v-else class="ml-auto text-xs text-fg-subtle">{{
            $t('friends.alreadyLinked')
          }}</span>
        </li>
      </ul>
      <p v-else-if="query.trim() && !searching" class="mt-3 text-sm text-fg-subtle">
        {{ $t('friends.noResults') }}
      </p>
    </UiCard>

    <section v-if="incoming.length">
      <h2 class="mb-2 text-sm font-semibold text-fg-muted">
        {{ $t('friends.incoming') }} ({{ incoming.length }})
      </h2>
      <UiCard>
        <ul class="divide-y divide-line-subtle">
          <li
            v-for="request in incoming"
            :key="request.friendship_id"
            class="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3"
          >
            <UiAvatar :name="request.user.display_name" :size="32" />
            <NuxtLink
              :to="`/users/${request.user.id}`"
              class="min-w-32 flex-1 truncate text-sm font-medium hover:underline"
            >
              {{ request.user.display_name }}
            </NuxtLink>
            <div class="ml-auto flex flex-wrap justify-end gap-2">
              <UiButton
                size="sm"
                :label="$t('friends.accept')"
                @click="guard(() => accept(request.friendship_id))"
              />
              <UiButton
                size="sm"
                variant="ghost"
                :label="$t('friends.decline')"
                @click="guard(() => remove(request.friendship_id))"
              />
            </div>
          </li>
        </ul>
      </UiCard>
    </section>

    <section v-if="outgoing.length">
      <h2 class="mb-2 text-sm font-semibold text-fg-muted">
        {{ $t('friends.outgoing') }} ({{ outgoing.length }})
      </h2>
      <UiCard>
        <ul class="divide-y divide-line-subtle">
          <li
            v-for="request in outgoing"
            :key="request.friendship_id"
            class="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3"
          >
            <UiAvatar :name="request.user.display_name" :size="32" />
            <span class="min-w-32 flex-1 truncate text-sm font-medium">
              {{ request.user.display_name }}
            </span>
            <div class="ml-auto flex items-center gap-3">
              <span class="text-xs text-fg-subtle">{{ $t('friends.pending') }}</span>
              <UiButton
                size="sm"
                variant="ghost"
                :label="$t('friends.cancel')"
                @click="guard(() => remove(request.friendship_id))"
              />
            </div>
          </li>
        </ul>
      </UiCard>
    </section>

    <section>
      <h2 class="mb-2 text-sm font-semibold text-fg-muted">
        {{ $t('friends.yourFriends') }} ({{ friends.length }})
      </h2>
      <UiCard>
        <p v-if="friends.length === 0" class="p-4 text-sm text-fg-subtle">
          {{ $t('friends.none') }}
        </p>
        <ul v-else class="divide-y divide-line-subtle">
          <li
            v-for="friend in friends"
            :key="friend.friendship_id"
            class="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3"
          >
            <UiAvatar :name="friend.user.display_name" :size="32" />
            <div class="min-w-32 flex-1">
              <NuxtLink
                :to="`/users/${friend.user.id}`"
                class="block truncate text-sm font-medium hover:underline"
              >
                {{ friend.user.display_name }}
              </NuxtLink>
              <UiPresenceDot :user-id="friend.user.id" label />
            </div>
            <div class="ml-auto flex flex-wrap justify-end gap-2">
              <NuxtLink :to="{ path: '/messages', query: { to: friend.user.id } }">
                <UiButton size="sm" variant="secondary" :label="$t('friends.message')" />
              </NuxtLink>
              <UiButton
                size="sm"
                variant="ghost"
                :label="$t('friends.remove')"
                @click="guard(() => remove(friend.friendship_id))"
              />
              <UiButton
                size="sm"
                variant="ghost"
                :label="$t('friends.block')"
                @click="guard(() => block(friend.user.id))"
              />
            </div>
          </li>
        </ul>
      </UiCard>
    </section>
  </div>
</template>
