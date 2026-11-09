<script setup lang="ts">
const { locale, locales, setLocale } = useI18n()
const { user, updateProfile } = useAuth()

function onChange(event: Event) {
  const code = (event.target as HTMLSelectElement).value
  setLocale(code as typeof locale.value)
  // Keeps the account's `locale` in step with the language actually shown.
  // The multiplayer draw reads it server-side (see ws.py's match.create),
  // where there is no request to attach `?locale=` to. Best-effort: a
  // logged-out visitor, or a request that fails, still gets the UI switch.
  if (user.value) {
    updateProfile({ locale: code as 'en' | 'fr' }).catch(() => {})
  }
}
</script>

<template>
  <label class="inline-flex items-center gap-2 sm:gap-3">
    <span class="sr-only">{{ $t('language.label') }}</span>
    <Icon
      name="lucide:languages"
      mode="svg"
      size="1.5em"
      aria-hidden="true"
      class="hidden flex-none min-[400px]:block"
    />
    <select
      :value="locale"
      class="bg-surface-card text-fg-body text-sm font-medium rounded-md border border-line-subtle px-2 py-1.5 transition-colors duration-slow hover:bg-surface-hover focus-visible:outline-none focus-visible:shadow-focus"
      @change="onChange"
    >
      <option v-for="item in locales" :key="item.code" :value="item.code">
        {{ item.name }}
      </option>
    </select>
  </label>
</template>
