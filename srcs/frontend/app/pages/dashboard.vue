<script setup lang="ts">
import type { LearningPath } from '~/types'
import type { AchievementOut, GamificationRules, UserStats } from '~/types/api'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const course = ref<LearningPath | null>(null)
const nextModule = computed(() => course.value?.modules.find((module) => !module.passed) ?? null)
const passedCount = computed(() => course.value?.modules.filter((m) => m.passed).length ?? 0)

const { user, fetchMe } = useAuth()
const { api } = useApi()
const { path } = useCourse()

const achievements = ref<AchievementOut[]>([])
const earnedCount = computed(() => achievements.value.filter((a) => a.earned_at).length)

const xpToNext = computed(() => (user.value ? user.value.xp_max - user.value.level_xp : 0))

const rules = ref<GamificationRules | null>(null)
const stats = ref<UserStats | null>(null)

onMounted(async () => {
  // `user` is cached since login: without a reload, XP won since would not show
  const [, list, fetchedRules, fetchedStats, fetchedCourse] = await Promise.all([
    fetchMe(true),
    api<AchievementOut[]>('/api/v1/users/me/achievements').catch(() => []),
    api<GamificationRules>('/api/v1/gamification/rules').catch(() => null),
    api<UserStats>('/api/v1/users/me/stats').catch(() => null),
    path().catch(() => null),
  ])
  achievements.value = list
  rules.value = fetchedRules
  stats.value = fetchedStats
  course.value = fetchedCourse
})
</script>

<template>
  <div v-if="user" class="mx-auto w-full max-w-260">
    <header class="mb-6 flex flex-wrap items-end justify-between gap-x-5 gap-y-3">
      <div>
        <p class="text-sm text-fg-subtle">{{ $t('dashboard.greeting') }}</p>
        <h1 class="text-2xl break-words sm:text-3xl">{{ user.display_name }} 👋</h1>
      </div>
      <UiTag
        v-if="user.streak > 0"
        type="streak"
        dot
        :label="$t('dashboard.streak', { n: user.streak })"
      />
    </header>

    <UiCard v-if="course" pad class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <div class="flex min-w-0 items-center gap-4">
        <span
          aria-hidden="true"
          class="flex size-12 flex-none items-center justify-center rounded-lg bg-accent-soft text-accent"
        >
          <Icon
            :name="nextModule ? moduleIcon(nextModule.slug) : 'lucide:orbit'"
            mode="svg"
            size="1.5em"
          />
        </span>
        <div class="min-w-0">
          <h2 class="text-lg font-semibold">{{ $t('dashboard.continueTitle') }}</h2>
          <p class="text-sm text-fg-muted">
            {{
              nextModule
                ? $t('dashboard.continueBody', { name: nextModule.name })
                : $t('dashboard.allPassed')
            }}
          </p>
          <p class="mt-1 font-mono text-xs text-fg-subtle">
            {{ $t('dashboard.modulesPassed', { n: passedCount, total: course.modules.length }) }}
          </p>
        </div>
      </div>
      <UiButton
        :label="$t('dashboard.continueAction')"
        :to="nextModule ? `/modules/${nextModule.slug}` : '/parcours'"
      />
    </UiCard>

    <div class="mb-5 grid gap-5 lg:grid-cols-[2fr_1fr]">
      <UiCard pad>
        <div class="mb-3.5 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <p class="text-lg font-semibold">{{ $t('dashboard.level', { n: user.level }) }}</p>
          <p class="font-mono text-xs text-fg-subtle">
            {{ $t('dashboard.xp', { current: user.level_xp, max: user.xp_max }) }}
          </p>
        </div>
        <UiProgress :value="user.level_xp" :max="user.xp_max" tone="xp" size="lg" />
        <p class="mt-2.5 text-xs text-fg-subtle">
          {{ $t('dashboard.xpToNext', { n: xpToNext, level: user.level + 1 }) }}
        </p>
        <details v-if="rules" class="mt-3 text-sm">
          <summary class="cursor-pointer text-fg-subtle">{{ $t('dashboard.rules.title') }}</summary>
          <ul class="mt-2 space-y-1">
            <li>{{ $t('dashboard.rules.quizCorrect', { n: rules.xp.quiz_correct }) }}</li>
            <li>{{ $t('dashboard.rules.modulePassed', { n: rules.xp.module_passed }) }}</li>
            <li>{{ $t('dashboard.rules.perLevel', { n: rules.xp_per_level }) }}</li>
            <li>{{ $t('dashboard.rules.streak') }}</li>
          </ul>
        </details>
      </UiCard>

      <UiCard v-if="stats" pad>
        <div class="flex gap-5">
          <UiStat :value="stats.solved" :label="$t('dashboard.statsSolved')" />
          <UiStat :value="stats.to_review" :label="$t('dashboard.statsToReview')" />
        </div>
      </UiCard>
    </div>

    <UiCard v-if="achievements.length" pad class="mb-5">
      <div class="mb-3.5 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 class="text-lg font-semibold">{{ $t('dashboard.achievements') }}</h2>
        <p class="font-mono text-xs text-fg-subtle">
          {{ $t('dashboard.achievementsCount', { n: earnedCount, total: achievements.length }) }}
        </p>
      </div>
      <ul class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <li
          v-for="achievement in achievements"
          :key="achievement.code"
          class="flex flex-col items-center gap-1 rounded-lg p-3 text-center"
          :class="achievement.earned_at ? 'bg-surface-raised' : 'opacity-40 grayscale'"
        >
          <span class="text-3xl" aria-hidden="true">
            {{ ACHIEVEMENT_ICONS[achievement.code] ?? '🏅' }}
          </span>
          <span class="text-sm font-medium">{{ $t(`achievements.${achievement.code}.name`) }}</span>
          <span class="text-xs text-fg-subtle">{{
            $t(`achievements.${achievement.code}.desc`)
          }}</span>
          <span v-if="!achievement.earned_at" class="sr-only">{{ $t('dashboard.locked') }}</span>
        </li>
      </ul>
    </UiCard>
  </div>
</template>
