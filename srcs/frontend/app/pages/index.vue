<script setup lang="ts">
definePageMeta({ layout: 'default' })

const PITCH = [
  { key: 'courses', icon: 'lucide:book-open' },
  { key: 'adaptive', icon: 'lucide:target' },
  { key: 'progress', icon: 'lucide:rocket' },
]

const STEPS = [
  { key: 'read', icon: 'lucide:book-open-text' },
  { key: 'check', icon: 'lucide:list-checks' },
  { key: 'validate', icon: 'lucide:badge-check' },
]

// The sample question of the landing page, its right answer shown as revealed
const SAMPLE_CHOICES = ['a', 'b', 'c', 'd'] as const
const SAMPLE_CORRECT = 'b'

const EYEBROW = 'text-xs font-semibold tracking-caps uppercase text-fg-subtle'
</script>

<template>
  <div class="flex w-full flex-col">
    <AppHeader>
      <NuxtLink to="/login" class="hidden sm:block">
        <UiButton variant="ghost" :label="$t('auth.login')" />
      </NuxtLink>
      <NuxtLink to="/sign-up" class="hidden sm:block">
        <UiButton :label="$t('auth.signUp')" />
      </NuxtLink>
    </AppHeader>

    <main class="flex flex-1 flex-col items-center px-4 pt-5 pb-5 sm:px-8 sm:pt-7">
      <section class="flex w-full max-w-350 flex-wrap items-center gap-8 sm:gap-12">
        <div class="min-w-0 flex-1 basis-105">
          <UiTag :label="$t('landing.badge')" />
          <h1 class="mb-4 text-3xl tracking-tight sm:text-4xl">{{ $t('landing.title') }}</h1>
          <p class="mb-5 max-w-140 text-lg leading-relaxed text-fg-muted">
            {{ $t('landing.subtitle') }}
          </p>
          <div class="flex flex-wrap gap-3">
            <NuxtLink to="/sign-up">
              <UiButton size="lg" :label="$t('landing.ctaPrimary')">
                <template #trailing>
                  <Icon name="lucide:arrow-right" mode="svg" size="1em" />
                </template>
              </UiButton>
            </NuxtLink>
            <NuxtLink to="/login">
              <UiButton size="lg" variant="secondary" :label="$t('landing.ctaSecondary')" />
            </NuxtLink>
          </div>
        </div>

        <ul class="flex min-w-0 flex-1 basis-85 flex-col gap-3.5">
          <li v-for="item in PITCH" :key="item.key">
            <UiCard pad>
              <div class="flex items-start gap-4">
                <span
                  aria-hidden="true"
                  class="flex size-11 flex-none items-center justify-center rounded-md bg-accent-soft text-accent"
                >
                  <Icon :name="item.icon" mode="svg" size="1.375em" />
                </span>
                <div>
                  <h3 class="mb-1 text-md">{{ $t(`landing.pitch.${item.key}.title`) }}</h3>
                  <p class="text-sm leading-normal text-fg-muted">
                    {{ $t(`landing.pitch.${item.key}.body`) }}
                  </p>
                </div>
              </div>
            </UiCard>
          </li>
        </ul>
      </section>

      <figure class="mt-10 w-full max-w-350 sm:mt-14">
        <div class="h-56 overflow-hidden rounded-lg border border-line-subtle shadow-lg sm:h-80">
          <GuianaScene :label="$t('landing.scene.alt')" />
        </div>
        <figcaption class="mt-2.5 text-sm text-fg-subtle">
          {{ $t('landing.scene.caption') }}
        </figcaption>
      </figure>

      <section class="mt-12 w-full max-w-350 sm:mt-16">
        <h2 class="mb-1.5 text-2xl font-semibold">{{ $t('landing.sample.title') }}</h2>
        <p class="mb-6 max-w-150 text-md text-fg-muted">
          {{ $t('landing.sample.subtitle') }}
        </p>

        <div class="grid items-start gap-8 lg:grid-cols-[minmax(0,620px)_minmax(0,1fr)]">
          <UiCard pad>
            <p class="mb-2" :class="EYEBROW">{{ $t('landing.sample.eyebrow') }}</p>
            <p class="mb-4 text-md leading-relaxed font-semibold">
              {{ $t('landing.sample.question') }}
            </p>
            <ul class="mb-4 flex flex-col gap-2">
              <li
                v-for="choice in SAMPLE_CHOICES"
                :key="choice"
                class="flex items-center justify-between gap-3 rounded-md border px-3.5 py-2.5 text-sm"
                :class="
                  choice === SAMPLE_CORRECT
                    ? 'border-success bg-success-soft font-semibold'
                    : 'border-line-subtle text-fg-muted'
                "
              >
                <span>{{ $t(`landing.sample.choices.${choice}`) }}</span>
                <span
                  v-if="choice === SAMPLE_CORRECT"
                  class="flex items-center gap-1.5 text-xs text-success"
                >
                  <Icon name="lucide:circle-check-big" mode="svg" size="1em" aria-hidden="true" />
                  {{ $t('landing.sample.correct') }}
                </span>
              </li>
            </ul>
            <p class="mb-2 text-sm leading-normal">{{ $t('landing.sample.explanation') }}</p>
            <p class="text-xs text-fg-subtle">{{ $t('landing.sample.source') }}</p>
          </UiCard>

          <div>
            <p class="mb-1.5" :class="EYEBROW">{{ $t('landing.how.eyebrow') }}</p>
            <h3 class="mb-3 text-xl font-semibold">{{ $t('landing.how.title') }}</h3>
            <ol class="flex flex-col">
              <li
                v-for="(step, index) in STEPS"
                :key="step.key"
                class="flex items-start gap-4 py-4"
                :class="index < STEPS.length - 1 ? 'border-b border-line-subtle' : ''"
              >
                <span
                  aria-hidden="true"
                  class="flex size-7 flex-none items-center justify-center rounded-md bg-accent-soft font-mono font-semibold text-accent"
                >
                  {{ index + 1 }}
                </span>
                <div>
                  <div class="mb-1 flex items-center gap-2">
                    <Icon
                      :name="step.icon"
                      mode="svg"
                      size="1.0625em"
                      aria-hidden="true"
                      class="text-accent"
                    />
                    <h4 class="text-md">{{ $t(`landing.how.${step.key}.title`) }}</h4>
                  </div>
                  <p class="text-sm leading-normal text-fg-muted">
                    {{ $t(`landing.how.${step.key}.body`) }}
                  </p>
                </div>
              </li>
            </ol>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
