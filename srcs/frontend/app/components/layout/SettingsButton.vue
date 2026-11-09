<script setup lang="ts">
const { user } = useAuth()

const avatarSrc = computed(() => user.value?.avatar_path ?? null)
</script>

<template>
  <div class="mx-3 mt-3 mb-2 border-t border-line-subtle pt-3">
    <NuxtLink
      to="/settings"
      :title="$t('nav.settings')"
      class="group flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors duration-slow ease-out hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:shadow-focus focus-visible:outline-none"
    >
      <UiAvatar :name="user?.display_name ?? ''" :src="avatarSrc" />
      <div class="min-w-0 flex-1">
        <p>{{ user?.display_name ?? '' }}</p>
        <p class="font-mono text-2xs font-regular text-fg-subtle">
          {{ user?.role ?? '' }}
        </p>
      </div>
      <Icon
        name="lucide:settings"
        mode="svg"
        size="1.25em"
        class="flex-none text-fg-subtle transition-transform duration-slow ease-out group-hover:rotate-45 group-hover:text-fg-body motion-reduce:transition-none"
        aria-hidden="true"
      />
      <span class="sr-only">{{ $t('nav.settings') }}</span>
    </NuxtLink>
  </div>
</template>
