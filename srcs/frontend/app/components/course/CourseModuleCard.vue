<script setup lang="ts">
import type { ModuleSummary } from '~/types'

const { module } = defineProps<{ module: ModuleSummary }>()
</script>

<template>
  <NuxtLink
    :to="`/modules/${module.slug}`"
    class="block h-full rounded-lg focus-visible:shadow-focus focus-visible:outline-none"
  >
    <UiCard pad interactive class="flex h-full flex-col gap-3">
      <div class="flex items-start gap-3.5">
        <span
          aria-hidden="true"
          class="flex size-11 flex-none items-center justify-center rounded-md"
          :class="module.passed ? 'bg-success-soft text-success' : 'bg-accent-soft text-accent'"
        >
          <Icon :name="moduleIcon(module.slug)" mode="svg" size="1.375em" />
        </span>
        <div class="min-w-0 flex-1">
          <p class="font-mono text-xs text-fg-subtle">
            {{ $t('course.moduleNumber', { n: module.position + 1 }) }}
          </p>
          <h3 class="text-md leading-snug font-semibold">{{ module.name }}</h3>
        </div>
        <UiTag v-if="module.passed" type="success" :label="$t('course.passed')" />
      </div>
      <p v-if="module.description" class="text-sm leading-normal text-fg-muted">
        {{ module.description }}
      </p>
      <div class="mt-auto flex flex-col gap-1.5">
        <div class="flex justify-between text-xs text-fg-subtle">
          <span>{{
            $t('course.lessonsRead', { n: module.lessons_read, total: module.lessons_total })
          }}</span>
          <span v-if="module.best_score !== null">
            {{ $t('course.bestScore', { n: percent(module.best_score) }) }}
          </span>
        </div>
        <UiProgress
          :value="module.lessons_read"
          :max="Math.max(1, module.lessons_total)"
          :tone="module.passed ? 'success' : 'accent'"
        />
      </div>
    </UiCard>
  </NuxtLink>
</template>
