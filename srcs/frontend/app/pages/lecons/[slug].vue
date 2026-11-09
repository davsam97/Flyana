<script setup lang="ts">
import type { Lesson } from '~/types'

definePageMeta({ layout: 'dashboard', middleware: 'auth' })

const route = useRoute()
const { t, locale } = useI18n()
const course = useCourse()
const { announce } = useAchievements()

const lesson = ref<Lesson | null>(null)
const failed = ref(false)
const end = ref<HTMLElement | null>(null)

const slug = computed(() => String(route.params.slug))

async function load() {
  failed.value = false
  try {
    lesson.value = await course.lesson(slug.value)
  } catch {
    failed.value = true
  }
}

/* A lesson counts as read once its end has scrolled into view */
let observer: IntersectionObserver | null = null

function watchEnd() {
  observer?.disconnect()
  if (!end.value || !lesson.value || lesson.value.read) return
  const current = lesson.value
  observer = new IntersectionObserver((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return
    observer?.disconnect()
    current.read = true
    course
      .markRead(current.slug)
      .then((outcome) => announce(outcome.achievements))
      .catch(() => {
        current.read = false
      })
  })
  observer.observe(end.value)
}

watch([lesson, end], () => nextTick(watchEnd))
onMounted(load)
watch([locale, slug], load)
onUnmounted(() => observer?.disconnect())

const breadcrumb = computed(() => [
  { label: t('nav.course'), to: '/parcours' },
  ...(lesson.value
    ? [
        { label: lesson.value.module_name, to: `/modules/${lesson.value.module_slug}` },
        { label: lesson.value.title },
      ]
    : []),
])
</script>

<template>
  <div class="mx-auto w-full max-w-190">
    <p v-if="failed" class="text-danger">{{ $t('course.loadFailed') }}</p>
    <article v-else-if="lesson">
      <UiBreadcrumb :items="breadcrumb" :label="$t('course.breadcrumb')" class="mb-4" />
      <p class="font-mono text-xs text-fg-subtle">
        {{ $t('course.lessonNumber', { n: lesson.position + 1 }) }}
      </p>
      <h1 class="mb-6 text-2xl sm:text-3xl">{{ lesson.title }}</h1>

      <CourseMarkdown :source="lesson.body" />

      <div
        ref="end"
        class="mt-10 flex flex-wrap justify-between gap-3 border-t border-line-subtle pt-5"
      >
        <UiButton
          v-if="lesson.previous_slug"
          variant="ghost"
          :label="$t('course.previousLesson')"
          :to="`/lecons/${lesson.previous_slug}`"
        />
        <span v-else />
        <UiButton
          v-if="lesson.next_slug"
          :label="$t('course.nextLesson')"
          :to="`/lecons/${lesson.next_slug}`"
        />
        <UiButton v-else :label="$t('course.toQuiz')" :to="`/modules/${lesson.module_slug}`" />
      </div>
    </article>
  </div>
</template>
