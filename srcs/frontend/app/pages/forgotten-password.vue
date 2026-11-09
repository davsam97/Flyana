<script setup lang="ts">
definePageMeta({ layout: 'default' })

const draftUsername = ref('')

function newpassword() {}
</script>

<template>
  <AuthShell
    :title="$t('auth.forgotTitle')"
    :subtitle="$t('auth.forgotSubtitle')"
    :alt-label="$t('auth.signIn')"
    alt-to="/login"
  >
    <form class="space-y-4" @submit.prevent="newpassword">
      <div>
        <label for="forgot-username" class="mb-1.5 block text-sm font-semibold">
          {{ $t('auth.username') }}
        </label>
        <UiInput
          id="forgot-username"
          v-model="draftUsername"
          type="text"
          required
          autocomplete="username"
          :placeholder="$t('auth.login42Placeholder')"
        />
      </div>
      <UiButton type="submit" block size="lg" :label="$t('auth.requestNewPassword')" />
    </form>
  </AuthShell>
</template>
